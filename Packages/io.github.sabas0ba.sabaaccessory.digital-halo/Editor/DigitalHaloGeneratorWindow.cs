using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace SabaAccessory.DigitalHalo.Editor
{
    internal enum DigitalHaloShape
    {
        Circle,
        Quad,
        Line,
        Wing,
    }

    internal sealed class DigitalHaloGeneratorWindow : EditorWindow
    {
        private const string HaloShaderName = "SabaAccessory/Digital Halo";
        private const string ParticleShaderName = "SabaAccessory/Digital Halo Particle";

        [SerializeField] private DigitalHaloShape shape = DigitalHaloShape.Circle;
        [SerializeField] private float radius = 0.34f;
        [SerializeField] private float radialSpan = 0.12f;
        [SerializeField] private int pointCount = 160;
        [SerializeField] private float heightOffset = 0.42f;
        [SerializeField] private Color lightColor = new Color(1.2f, 1.2f, 1.2f, 1f);
        [SerializeField] private Color glitchColor = new Color(0.52f, 0.52f, 0.52f, 1f);
        [SerializeField] private float glitchAmount = 0.62f;

        [MenuItem("Tools/SabaAccessory/Digital Halo Generator")]
        private static void Open()
        {
            DigitalHaloGeneratorWindow window = GetWindow<DigitalHaloGeneratorWindow>();
            window.titleContent = new GUIContent("Digital Halo");
            window.minSize = new Vector2(380f, 390f);
            window.Show();
        }

        private void OnGUI()
        {
            EditorGUILayout.LabelField("Geometry Block Halo Generator", EditorStyles.boldLabel);
            EditorGUILayout.Space();

            Transform parent = Selection.activeTransform;
            using (new EditorGUI.DisabledScope(true))
            {
                EditorGUILayout.ObjectField("Parent", parent, typeof(Transform), true);
            }

            if (parent == null)
            {
                EditorGUILayout.HelpBox(
                    "Head bone を選択してから生成すると、その子として地面と平行に配置されます。",
                    MessageType.Info
                );
            }

            shape = (DigitalHaloShape)EditorGUILayout.EnumPopup("Shape", shape);
            radius = EditorGUILayout.Slider("Size", radius, 0.05f, 1.5f);
            radialSpan = EditorGUILayout.Slider("Radial Span", radialSpan, 0.01f, 0.4f);
            pointCount = EditorGUILayout.IntSlider("Source Points", pointCount, 32, 256);
            heightOffset = EditorGUILayout.Slider("Height Offset", heightOffset, -0.5f, 1.0f);
            lightColor = EditorGUILayout.ColorField(
                new GUIContent("Color Range Max"),
                lightColor,
                true,
                false,
                true
            );
            glitchColor = EditorGUILayout.ColorField(
                new GUIContent("Color Range Min"),
                glitchColor,
                true,
                false,
                true
            );
            glitchAmount = EditorGUILayout.Slider("Randomness", glitchAmount, 0f, 1f);

            EditorGUILayout.Space();
            EditorGUILayout.HelpBox(
                "Geometry Shader を使用する PC Avatar 専用 Props です。Android/Quest では動作しません。",
                MessageType.Warning
            );

            Shader haloShader = Shader.Find(HaloShaderName);
            Shader particleShader = Shader.Find(ParticleShaderName);
            using (new EditorGUI.DisabledScope(haloShader == null || particleShader == null))
            {
                if (GUILayout.Button("Create Digital Halo", GUILayout.Height(34f)))
                {
                    DigitalHaloAssetBuilder.Create(
                        parent,
                        shape,
                        radius,
                        radialSpan,
                        pointCount,
                        heightOffset,
                        lightColor,
                        glitchColor,
                        glitchAmount,
                        haloShader,
                        particleShader
                    );
                }
            }

            if (haloShader == null || particleShader == null)
            {
                EditorGUILayout.HelpBox(
                    "Digital Halo shaders が見つかりません。Unity の import 完了後に再度開いてください。",
                    MessageType.Error
                );
            }
        }
    }

    internal static class DigitalHaloAssetBuilder
    {
        private const string GeneratedRoot = "Assets/SabaAccessory/Generated";

        internal static void Create(
            Transform parent,
            DigitalHaloShape shape,
            float radius,
            float radialSpan,
            int pointCount,
            float heightOffset,
            Color lightColor,
            Color glitchColor,
            float randomness,
            Shader haloShader,
            Shader particleShader
        )
        {
            if (haloShader == null)
            {
                throw new System.ArgumentNullException(nameof(haloShader));
            }
            if (particleShader == null)
            {
                throw new System.ArgumentNullException(nameof(particleShader));
            }

            EnsureFolder(GeneratedRoot);

            Mesh mesh = BuildPointCloud(shape, radius, radialSpan, pointCount);
            string meshPath = AssetDatabase.GenerateUniqueAssetPath(
                $"{GeneratedRoot}/DigitalHaloPointCloud.asset"
            );
            AssetDatabase.CreateAsset(mesh, meshPath);

            Material haloMaterial = BuildHaloMaterial(
                haloShader,
                lightColor,
                glitchColor,
                randomness
            );
            string haloMaterialPath = AssetDatabase.GenerateUniqueAssetPath(
                $"{GeneratedRoot}/DigitalHaloMaterial.mat"
            );
            AssetDatabase.CreateAsset(haloMaterial, haloMaterialPath);

            Material particleMaterial = BuildParticleMaterial(particleShader, lightColor);
            string particleMaterialPath = AssetDatabase.GenerateUniqueAssetPath(
                $"{GeneratedRoot}/DigitalHaloParticleMaterial.mat"
            );
            AssetDatabase.CreateAsset(particleMaterial, particleMaterialPath);

            GameObject halo = new GameObject("Digital Halo " + shape);
            Undo.RegisterCreatedObjectUndo(halo, "Create Digital Halo");
            if (parent != null)
            {
                Undo.SetTransformParent(halo.transform, parent, "Parent Digital Halo");
            }

            halo.transform.localPosition = Vector3.up * heightOffset;
            halo.transform.localRotation = Quaternion.identity;
            halo.transform.localScale = Vector3.one;

            MeshFilter meshFilter = Undo.AddComponent<MeshFilter>(halo);
            MeshRenderer meshRenderer = Undo.AddComponent<MeshRenderer>(halo);
            meshFilter.sharedMesh = mesh;
            meshRenderer.sharedMaterial = haloMaterial;
            ConfigureRenderer(meshRenderer);

            CreateParticles(halo.transform, mesh, particleMaterial);

            AssetDatabase.SaveAssets();
            Selection.activeGameObject = halo;
            EditorGUIUtility.PingObject(halo);
        }

        private static Material BuildHaloMaterial(
            Shader shader,
            Color lightColor,
            Color glitchColor,
            float randomness
        )
        {
            Material material = new Material(shader)
            {
                name = "DigitalHaloMaterial",
                renderQueue = (int)RenderQueue.Transparent,
            };
            material.SetFloat("_ColorMode", 0f);
            material.SetFloat("_PalettePreset", 0f);
            material.SetColor("_ColorMin", glitchColor);
            material.SetColor("_ColorMax", lightColor);
            material.SetColor("_DarkColor", new Color(0.006f, 0.007f, 0.009f, 0.88f));
            material.SetFloat("_Opacity", 0.92f);
            material.SetFloat("_Emission", 0.75f);
            material.SetFloat("_RectWidthMin", 0.018f);
            material.SetFloat("_RectWidthMax", 0.11f);
            material.SetFloat("_RectDepthMin", 0.008f);
            material.SetFloat("_RectDepthMax", 0.052f);
            material.SetFloat("_RectHeightMin", 0.012f);
            material.SetFloat("_RectHeightMax", 0.09f);
            material.SetFloat("_VerticalRectRatio", 0.42f);
            material.SetFloat("_SizeRandomness", randomness);
            material.SetFloat("_HorizontalOffsetMin", -0.075f);
            material.SetFloat("_HorizontalOffsetMax", 0.075f);
            material.SetFloat("_HorizontalRandomness", randomness);
            material.SetFloat("_VerticalOffsetMin", -0.035f);
            material.SetFloat("_VerticalOffsetMax", 0.055f);
            material.SetFloat("_VerticalRandomness", randomness);
            material.SetFloat("_WorldNoiseScale", 18f);
            material.SetFloat("_FlickerSpeed", 4.5f);
            material.SetFloat("_SpawnProbability", 0.48f);
            material.SetFloat("_OverlapCount", 3f);
            material.SetFloat("_RandomSeed", 17f);
            material.SetFloat("_RectDistortion", 0.008f);
            material.SetFloat("_DistortionSpeed", 3.5f);
            material.SetFloat("_SurfaceWarp", 0.035f);
            material.SetFloat("_EdgeBlur", 0.055f);
            material.SetFloat("_RectHaze", 0.24f);
            material.SetFloat("_RectDissolve", 0.12f);
            return material;
        }

        private static Material BuildParticleMaterial(Shader shader, Color lightColor)
        {
            Material material = new Material(shader)
            {
                name = "DigitalHaloParticleMaterial",
                renderQueue = (int)RenderQueue.Transparent + 1,
            };
            material.SetColor("_Color", lightColor);
            material.SetFloat("_Emission", 0.55f);
            material.SetFloat("_Opacity", 0.42f);
            return material;
        }

        private static Mesh BuildPointCloud(
            DigitalHaloShape shape,
            float radius,
            float radialSpan,
            int pointCount
        )
        {
            float clampedRadius = Mathf.Max(0.01f, radius);
            float clampedSpan = Mathf.Clamp(radialSpan, 0.001f, clampedRadius * 0.95f);
            int clampedCount = Mathf.Clamp(pointCount, 8, 512);

            List<Vector3> vertices = new List<Vector3>(clampedCount);
            List<Vector3> normals = new List<Vector3>(clampedCount);
            List<Vector2> uv = new List<Vector2>(clampedCount);
            List<Vector2> randomUv = new List<Vector2>(clampedCount);
            List<Vector2> directionUv = new List<Vector2>(clampedCount);
            int[] indices = new int[clampedCount];

            for (int index = 0; index < clampedCount; index++)
            {
                float seed = Hash01(index * 37 + 11);
                float ratio;
                Vector3 position;
                Vector3 tangent;
                BuildShapePoint(
                    shape,
                    index,
                    clampedCount,
                    clampedRadius,
                    clampedSpan,
                    out ratio,
                    out position,
                    out tangent
                );
                vertices.Add(position);
                normals.Add(Vector3.up);
                uv.Add(new Vector2(ratio, seed));
                randomUv.Add(
                    new Vector2(Hash01(index * 89 + 23), Hash01(index * 97 + 29))
                );
                directionUv.Add(new Vector2(tangent.x, tangent.z));
                indices[index] = index;
            }

            Mesh mesh = new Mesh { name = "DigitalHalo" + shape + "PointCloud" };
            mesh.SetVertices(vertices);
            mesh.SetNormals(normals);
            mesh.SetUVs(0, uv);
            mesh.SetUVs(1, randomUv);
            mesh.SetUVs(2, directionUv);
            mesh.SetIndices(indices, MeshTopology.Points, 0, false);
            float extent = clampedRadius + clampedSpan + 0.25f;
            // Rectangles are emitted in world XZ regardless of the parent rotation.
            // A conservative cube keeps Unity culling bounds valid for rotated Head bones.
            float boundExtent = extent + 0.5f;
            mesh.bounds = new Bounds(Vector3.zero, new Vector3(boundExtent * 2f, boundExtent * 2f, boundExtent * 2f));
            return mesh;
        }

        private static void BuildShapePoint(
            DigitalHaloShape shape,
            int index,
            int count,
            float size,
            float span,
            out float ratio,
            out Vector3 position,
            out Vector3 tangent
        )
        {
            float jitter = Hash01(index * 53 + 7);
            ratio = (index + jitter * 0.82f) / count;
            if (shape == DigitalHaloShape.Circle)
            {
                float angle = ratio * Mathf.PI * 2f;
                float pointRadius = size + (Hash01(index * 71 + 19) - 0.5f) * span;
                position = new Vector3(
                    Mathf.Cos(angle) * pointRadius,
                    0f,
                    Mathf.Sin(angle) * pointRadius
                );
                tangent = new Vector3(-Mathf.Sin(angle), 0f, Mathf.Cos(angle));
                return;
            }

            if (shape == DigitalHaloShape.Quad)
            {
                float perimeter = ratio * 4f;
                int side = Mathf.Min(Mathf.FloorToInt(perimeter), 3);
                float sideRatio = perimeter - side;
                if (side == 0)
                {
                    position = new Vector3(Mathf.Lerp(-size, size, sideRatio), 0f, -size);
                    tangent = Vector3.right;
                }
                else if (side == 1)
                {
                    position = new Vector3(size, 0f, Mathf.Lerp(-size, size, sideRatio));
                    tangent = Vector3.forward;
                }
                else if (side == 2)
                {
                    position = new Vector3(Mathf.Lerp(size, -size, sideRatio), 0f, size);
                    tangent = Vector3.left;
                }
                else
                {
                    position = new Vector3(-size, 0f, Mathf.Lerp(size, -size, sideRatio));
                    tangent = Vector3.back;
                }
                Vector3 outward = new Vector3(tangent.z, 0f, -tangent.x);
                position += outward * (Hash01(index * 71 + 19) - 0.5f) * span;
                return;
            }

            if (shape == DigitalHaloShape.Line)
            {
                position = new Vector3(
                    Mathf.Lerp(-size, size, ratio),
                    0f,
                    (Hash01(index * 71 + 19) - 0.5f) * span
                );
                tangent = Vector3.right;
                return;
            }

            int pairCount = Mathf.Max((count + 1) / 2, 1);
            int pairIndex = index / 2;
            float wingRatio = (pairIndex + jitter * 0.72f) / pairCount;
            float wingSide = index % 2 == 0 ? -1f : 1f;
            float x = wingSide * size * (0.14f + wingRatio * 0.9f);
            float z = size
                * (Mathf.Sin(wingRatio * Mathf.PI) * 0.48f + (wingRatio - 0.5f) * 0.18f);
            tangent = new Vector3(
                wingSide * 0.9f,
                0f,
                Mathf.Cos(wingRatio * Mathf.PI) * Mathf.PI * 0.48f + 0.18f
            ).normalized;
            Vector3 wingNormal = new Vector3(tangent.z, 0f, -tangent.x);
            position = new Vector3(x, 0f, z)
                + wingNormal * (Hash01(index * 71 + 19) - 0.5f) * span;
            ratio = wingRatio;
        }

        private static void CreateParticles(
            Transform parent,
            Mesh sourceMesh,
            Material material
        )
        {
            GameObject particleObject = new GameObject("Block Noise Particles");
            Undo.RegisterCreatedObjectUndo(particleObject, "Create Digital Halo Particles");
            Undo.SetTransformParent(particleObject.transform, parent, "Parent Digital Halo Particles");
            particleObject.transform.localPosition = Vector3.zero;
            particleObject.transform.localRotation = Quaternion.identity;
            particleObject.transform.localScale = Vector3.one;

            ParticleSystem particles = Undo.AddComponent<ParticleSystem>(particleObject);
            ParticleSystem.MainModule main = particles.main;
            main.loop = true;
            main.prewarm = true;
            main.startLifetime = new ParticleSystem.MinMaxCurve(0.24f, 0.82f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(0.015f, 0.07f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.01f, 0.045f);
            main.startColor = new ParticleSystem.MinMaxGradient(
                new Color(0.32f, 0.32f, 0.32f, 0.18f),
                new Color(1f, 1f, 1f, 0.52f)
            );
            main.maxParticles = 120;
            main.simulationSpace = ParticleSystemSimulationSpace.Local;
            main.scalingMode = ParticleSystemScalingMode.Hierarchy;
            main.playOnAwake = true;

            ParticleSystem.EmissionModule emission = particles.emission;
            emission.rateOverTime = 42f;

            ParticleSystem.ShapeModule shape = particles.shape;
            shape.enabled = true;
            shape.shapeType = ParticleSystemShapeType.Mesh;
            shape.mesh = sourceMesh;
            shape.meshShapeType = ParticleSystemMeshShapeType.Vertex;

            ParticleSystem.ColorOverLifetimeModule colorOverLifetime = particles.colorOverLifetime;
            colorOverLifetime.enabled = true;
            Gradient alphaGradient = new Gradient();
            alphaGradient.SetKeys(
                new[]
                {
                    new GradientColorKey(Color.white, 0f),
                    new GradientColorKey(Color.white, 1f),
                },
                new[]
                {
                    new GradientAlphaKey(0f, 0f),
                    new GradientAlphaKey(1f, 0.18f),
                    new GradientAlphaKey(0.62f, 0.62f),
                    new GradientAlphaKey(0f, 1f),
                }
            );
            colorOverLifetime.color = new ParticleSystem.MinMaxGradient(alphaGradient);

            ParticleSystemRenderer renderer = particleObject.GetComponent<ParticleSystemRenderer>();
            renderer.sharedMaterial = material;
            renderer.renderMode = ParticleSystemRenderMode.Billboard;
            renderer.alignment = ParticleSystemRenderSpace.View;
            renderer.sortMode = ParticleSystemSortMode.YoungestInFront;
            ConfigureRenderer(renderer);
        }

        private static void ConfigureRenderer(Renderer renderer)
        {
            renderer.shadowCastingMode = ShadowCastingMode.Off;
            renderer.receiveShadows = false;
            renderer.lightProbeUsage = LightProbeUsage.Off;
            renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
            renderer.motionVectorGenerationMode = MotionVectorGenerationMode.ForceNoMotion;
            renderer.allowOcclusionWhenDynamic = false;
        }

        private static void EnsureFolder(string folderPath)
        {
            string[] parts = folderPath.Split('/');
            string current = parts[0];
            for (int index = 1; index < parts.Length; index++)
            {
                string next = current + "/" + parts[index];
                if (!AssetDatabase.IsValidFolder(next))
                {
                    AssetDatabase.CreateFolder(current, parts[index]);
                }
                current = next;
            }
        }

        private static float Hash01(int value)
        {
            unchecked
            {
                uint hash = (uint)value;
                hash ^= hash >> 16;
                hash *= 0x7feb352d;
                hash ^= hash >> 15;
                hash *= 0x846ca68b;
                hash ^= hash >> 16;
                return (hash & 0x00ffffff) / 16777215f;
            }
        }
    }
}
