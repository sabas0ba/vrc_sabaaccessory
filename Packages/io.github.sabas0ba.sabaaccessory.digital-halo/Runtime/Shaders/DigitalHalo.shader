Shader "SabaAccessory/Digital Halo"
{
    Properties
    {
        [Enum(Monochrome,0,Fixed Palette,1,Single Color,2,Color Range,3)] _ColorMode ("Color Mode", Float) = 0
        [Enum(Neutral,0,Cold Steel,1,Amber,2,Violet,3,Terminal,4)] _PalettePreset ("Fixed Palette", Float) = 0
        [HDR] _ColorMin ("Color Range Min", Color) = (0.08, 0.08, 0.08, 1)
        [HDR] _ColorMax ("Color Range Max", Color) = (1.2, 1.2, 1.2, 1)
        _DarkColor ("Monochrome Lower", Color) = (0.006, 0.007, 0.009, 0.88)
        _Opacity ("Opacity", Range(0, 1)) = 0.92
        _Emission ("Emission", Range(0, 4)) = 0.75

        _RectWidthMin ("Rectangle Width Min", Range(0.001, 0.3)) = 0.018
        _RectWidthMax ("Rectangle Width Max", Range(0.001, 0.3)) = 0.11
        _RectDepthMin ("Horizontal Depth Min", Range(0.001, 0.2)) = 0.008
        _RectDepthMax ("Horizontal Depth Max", Range(0.001, 0.2)) = 0.052
        _RectHeightMin ("Vertical Height Min", Range(0.001, 0.3)) = 0.012
        _RectHeightMax ("Vertical Height Max", Range(0.001, 0.3)) = 0.09
        _VerticalRectRatio ("Vertical Rectangle Ratio", Range(0, 1)) = 0.42
        _SizeRandomness ("Size Randomness", Range(0, 1)) = 0.62

        _HorizontalOffsetMin ("World Horizontal Glitch Min", Range(-0.3, 0.3)) = -0.075
        _HorizontalOffsetMax ("World Horizontal Glitch Max", Range(-0.3, 0.3)) = 0.075
        _HorizontalRandomness ("Horizontal Randomness", Range(0, 1)) = 0.62
        _VerticalOffsetMin ("World Appearance Height Min", Range(-0.2, 0.2)) = -0.035
        _VerticalOffsetMax ("World Appearance Height Max", Range(-0.2, 0.2)) = 0.055
        _VerticalRandomness ("Height Randomness", Range(0, 1)) = 0.62
        _WorldNoiseScale ("World Noise Scale", Range(0.1, 100)) = 18

        _FlickerSpeed ("Appearance Rate", Range(0.1, 20)) = 4.5
        _SpawnProbability ("Spawn Probability", Range(0, 1)) = 0.48
        _OverlapCount ("Maximum Overlap", Range(1, 3)) = 3
        _RandomSeed ("Random Seed", Range(0, 1000)) = 17

        _RectDistortion ("Per Rectangle Distortion", Range(0, 0.08)) = 0.008
        _DistortionSpeed ("Distortion Speed", Range(0, 20)) = 3.5
        _SurfaceWarp ("Surface Warp", Range(0, 0.25)) = 0.035
        _EdgeBlur ("Edge Blur", Range(0.001, 0.3)) = 0.055
        _RectHaze ("Rectangle Haze", Range(0, 1)) = 0.24
        _RectDissolve ("Rectangle Dissolve", Range(0, 1)) = 0.12
    }

    SubShader
    {
        Tags
        {
            "Queue" = "Transparent"
            "RenderType" = "Transparent"
            "IgnoreProjector" = "True"
            "DisableBatching" = "True"
            "VRCFallback" = "UnlitTransparent"
        }

        CGINCLUDE
        #include "UnityCG.cginc"

        float _ColorMode;
        float _PalettePreset;
        float4 _ColorMin;
        float4 _ColorMax;
        float4 _DarkColor;
        float _Opacity;
        float _Emission;
        float _RectWidthMin;
        float _RectWidthMax;
        float _RectDepthMin;
        float _RectDepthMax;
        float _RectHeightMin;
        float _RectHeightMax;
        float _VerticalRectRatio;
        float _SizeRandomness;
        float _HorizontalOffsetMin;
        float _HorizontalOffsetMax;
        float _HorizontalRandomness;
        float _VerticalOffsetMin;
        float _VerticalOffsetMax;
        float _VerticalRandomness;
        float _WorldNoiseScale;
        float _FlickerSpeed;
        float _SpawnProbability;
        float _OverlapCount;
        float _RandomSeed;
        float _RectDistortion;
        float _DistortionSpeed;
        float _SurfaceWarp;
        float _EdgeBlur;
        float _RectHaze;
        float _RectDissolve;

        struct appdata
        {
            float4 vertex : POSITION;
            float2 uv : TEXCOORD0;
            float2 randomUv : TEXCOORD1;
            float2 direction : TEXCOORD2;
        };

        struct v2g
        {
            float4 position : SV_POSITION;
            float4 seeds : TEXCOORD0;
            float2 direction : TEXCOORD1;
        };

        struct g2f
        {
            float4 position : SV_POSITION;
            float2 uv : TEXCOORD0;
            float4 style : TEXCOORD1;
            float3 worldPosition : TEXCOORD2;
        };

        float hash12(float2 value)
        {
            float3 p = frac(float3(value.xyx) * 0.1031);
            p += dot(p, p.yzx + 33.33);
            return frac((p.x + p.y) * p.z);
        }

        float hash13(float3 value)
        {
            value = frac(value * 0.1031);
            value += dot(value, value.zyx + 31.32);
            return frac((value.x + value.y) * value.z);
        }

        float randomRange(float minimum, float maximum, float noise, float randomness)
        {
            float lower = min(minimum, maximum);
            float upper = max(minimum, maximum);
            float midpoint = (lower + upper) * 0.5;
            return lerp(midpoint, lerp(lower, upper, noise), saturate(randomness));
        }

        v2g vert(appdata input)
        {
            v2g output;
            output.position = input.vertex;
            output.seeds = float4(input.uv, input.randomUv);
            output.direction = input.direction;
            return output;
        }

        float3 distortCorner(
            float3 position,
            float3 axisA,
            float3 axisB,
            float3 normal,
            float seed,
            float corner
        )
        {
            float3 cell = floor(position * max(_WorldNoiseScale, 0.1));
            float phase = _Time.y * _DistortionSpeed;
            float noiseA = hash13(cell + float3(seed, corner * 7.0, 11.0));
            float noiseB = hash13(cell + float3(17.0, seed, corner * 13.0));
            float noiseC = hash13(cell + float3(corner * 19.0, 23.0, seed));
            float waveA = sin(phase + noiseA * 6.2831853);
            float waveB = sin(phase * 1.17 + noiseB * 6.2831853);
            float waveC = sin(phase * 0.83 + noiseC * 6.2831853);
            return position + (axisA * waveA + axisB * waveB + normal * waveC)
                * _RectDistortion;
        }

        g2f makeGeometryVertex(
            float3 worldPosition,
            float2 uv,
            float seed,
            float brightness,
            float vertical,
            float activity
        )
        {
            g2f output;
            output.position = UnityWorldToClipPos(worldPosition);
            output.uv = uv;
            output.style = float4(seed, brightness, vertical, activity);
            output.worldPosition = worldPosition;
            return output;
        }

        [maxvertexcount(12)]
        void geom(point v2g input[1], inout TriangleStream<g2f> stream)
        {
            float3 worldOrigin = mul(unity_ObjectToWorld, float4(0, 0, 0, 1)).xyz;
            float scaleX = length(mul((float3x3)unity_ObjectToWorld, float3(1, 0, 0)));
            float scaleZ = length(mul((float3x3)unity_ObjectToWorld, float3(0, 0, 1)));
            float2 localTangent = normalize(input[0].direction + float2(0.00001, 0.00001));
            float3 tangent = float3(localTangent.x, 0.0, localTangent.y);
            float3 radial = float3(tangent.z, 0.0, -tangent.x);
            float3 worldUp = float3(0.0, 1.0, 0.0);
            float3 baseWorld = worldOrigin
                + float3(
                    input[0].position.x * max(scaleX, 0.0001),
                    0.0,
                    input[0].position.z * max(scaleZ, 0.0001)
                );
            float3 worldCell = floor(baseWorld * max(_WorldNoiseScale, 0.1));
            float worldSeed = hash13(worldCell + _RandomSeed) * 997.0;
            float sourceSeed = input[0].seeds.y * 173.0
                + input[0].seeds.z * 61.0
                + input[0].seeds.w * 29.0
                + worldSeed;

            [unroll]
            for (int layer = 0; layer < 3; layer++)
            {
                if ((float)layer >= _OverlapCount)
                {
                    continue;
                }

                float layerSeed = sourceSeed + layer * 47.13;
                float timeValue = _Time.y * max(_FlickerSpeed, 0.01) + layerSeed * 0.071;
                float cycle = floor(timeValue);
                float phase = frac(timeValue);
                float spawnNoise = hash12(float2(layerSeed, cycle + worldSeed));
                if (spawnNoise > _SpawnProbability)
                {
                    continue;
                }

                float widthNoise = hash12(float2(layerSeed + 11.0, cycle + 7.0));
                float depthNoise = hash12(float2(layerSeed + 19.0, cycle + 13.0));
                float heightNoise = hash12(float2(layerSeed + 23.0, cycle + 15.0));
                float horizontalNoise = hash12(float2(layerSeed + 31.0, cycle + 17.0));
                float verticalNoise = hash12(float2(layerSeed + 41.0, cycle + 23.0));
                float radialNoise = hash12(float2(layerSeed + 53.0, cycle + 29.0)) - 0.5;
                float brightness = hash12(float2(layerSeed + 67.0, cycle + 37.0));
                float orientationNoise = hash12(float2(layerSeed + 73.0, cycle + 41.0));
                float verticalRectangle = step(orientationNoise, saturate(_VerticalRectRatio));

                float rectangleWidth = randomRange(
                    _RectWidthMin,
                    _RectWidthMax,
                    widthNoise,
                    _SizeRandomness
                );
                float rectangleDepth = randomRange(
                    _RectDepthMin,
                    _RectDepthMax,
                    depthNoise,
                    _SizeRandomness
                );
                float rectangleHeight = randomRange(
                    _RectHeightMin,
                    _RectHeightMax,
                    heightNoise,
                    _SizeRandomness
                );
                float horizontalOffset = randomRange(
                    _HorizontalOffsetMin,
                    _HorizontalOffsetMax,
                    horizontalNoise,
                    _HorizontalRandomness
                );
                float verticalOffset = randomRange(
                    _VerticalOffsetMin,
                    _VerticalOffsetMax,
                    verticalNoise,
                    _VerticalRandomness
                );

                float activity = smoothstep(0.0, 0.12, phase)
                    * (1.0 - smoothstep(0.68, 1.0, phase));
                float3 center = baseWorld
                    + tangent * horizontalOffset
                    + radial * radialNoise * rectangleDepth * 1.8;
                center.y += verticalOffset;

                float3 axisA = tangent;
                float3 axisB = lerp(radial, worldUp, verticalRectangle);
                float3 normal = lerp(worldUp, radial, verticalRectangle);
                float3 along = axisA * rectangleWidth * 0.5;
                float secondarySize = lerp(rectangleDepth, rectangleHeight, verticalRectangle);
                float3 across = axisB * secondarySize * 0.5;

                float3 p0 = distortCorner(center - along - across, axisA, axisB, normal, layerSeed, 0.0);
                float3 p1 = distortCorner(center + along - across, axisA, axisB, normal, layerSeed, 1.0);
                float3 p2 = distortCorner(center - along + across, axisA, axisB, normal, layerSeed, 2.0);
                float3 p3 = distortCorner(center + along + across, axisA, axisB, normal, layerSeed, 3.0);
                stream.Append(makeGeometryVertex(p0, float2(0, 0), layerSeed, brightness, verticalRectangle, activity));
                stream.Append(makeGeometryVertex(p1, float2(1, 0), layerSeed, brightness, verticalRectangle, activity));
                stream.Append(makeGeometryVertex(p2, float2(0, 1), layerSeed, brightness, verticalRectangle, activity));
                stream.Append(makeGeometryVertex(p3, float2(1, 1), layerSeed, brightness, verticalRectangle, activity));
                stream.RestartStrip();
            }
        }

        float3 fixedPalette(float value)
        {
            float3 low;
            float3 middle;
            float3 high;
            if (_PalettePreset < 0.5)
            {
                low = float3(0.015, 0.017, 0.022);
                middle = float3(0.32, 0.34, 0.38);
                high = float3(1.0, 1.0, 1.0);
            }
            else if (_PalettePreset < 1.5)
            {
                low = float3(0.01, 0.025, 0.04);
                middle = float3(0.18, 0.42, 0.62);
                high = float3(0.76, 0.92, 1.0);
            }
            else if (_PalettePreset < 2.5)
            {
                low = float3(0.045, 0.018, 0.004);
                middle = float3(0.72, 0.25, 0.025);
                high = float3(1.0, 0.74, 0.28);
            }
            else if (_PalettePreset < 3.5)
            {
                low = float3(0.025, 0.008, 0.055);
                middle = float3(0.42, 0.16, 0.68);
                high = float3(0.86, 0.68, 1.0);
            }
            else
            {
                low = float3(0.005, 0.035, 0.018);
                middle = float3(0.06, 0.52, 0.26);
                high = float3(0.62, 1.0, 0.76);
            }
            return value < 0.5
                ? lerp(low, middle, value * 2.0)
                : lerp(middle, high, (value - 0.5) * 2.0);
        }

        float3 resolveColor(float value)
        {
            if (_ColorMode < 0.5)
            {
                return lerp(_DarkColor.rgb, float3(1.0, 1.0, 1.0), value);
            }
            if (_ColorMode < 1.5)
            {
                return fixedPalette(value);
            }
            if (_ColorMode < 2.5)
            {
                return _ColorMax.rgb;
            }
            return lerp(_ColorMin.rgb, _ColorMax.rgb, value);
        }

        void evaluateRectangle(
            g2f input,
            out float interior,
            out float dissolve,
            out float haze
        )
        {
            float3 worldCell = floor(input.worldPosition * max(_WorldNoiseScale, 0.1));
            float timeCell = floor(_Time.y * max(_DistortionSpeed, 0.01));
            float noiseA = hash13(worldCell + float3(input.style.x, timeCell, 17.0));
            float noiseB = hash13(worldCell + float3(23.0, input.style.x, timeCell));
            float2 warpedUv = input.uv + (float2(noiseA, noiseB) - 0.5) * _SurfaceWarp;
            float softness = max(_EdgeBlur, 0.001);
            float2 lower = smoothstep(0.0, softness, warpedUv);
            float2 upper = 1.0 - smoothstep(1.0 - softness, 1.0, warpedUv);
            interior = lower.x * lower.y * upper.x * upper.y;
            float threshold = saturate(_RectDissolve * 0.88);
            dissolve = smoothstep(threshold, min(threshold + 0.14, 1.0), noiseA);
            haze = lerp(1.0, lerp(0.22, 1.0, noiseB), _RectHaze);
        }

        float4 fragBody(g2f input) : SV_Target
        {
            float interior;
            float dissolve;
            float haze;
            evaluateRectangle(input, interior, dissolve, haze);
            float3 color = resolveColor(input.style.y);
            float brightnessAlpha = lerp(0.48, 1.0, input.style.y);
            float alpha = input.style.w * interior * dissolve * haze
                * brightnessAlpha * _Opacity;
            return float4(color, saturate(alpha));
        }

        float4 fragGlow(g2f input) : SV_Target
        {
            float interior;
            float dissolve;
            float haze;
            evaluateRectangle(input, interior, dissolve, haze);
            float luminous = smoothstep(0.68, 0.92, input.style.y);
            float alpha = input.style.w * luminous * interior * dissolve * haze
                * 0.14 * _Emission * _Opacity;
            return float4(resolveColor(input.style.y) * _Emission, saturate(alpha));
        }
        ENDCG

        Pass
        {
            Name "World Blocks"
            Blend SrcAlpha OneMinusSrcAlpha
            Cull Off
            ZWrite Off
            ZTest LEqual

            CGPROGRAM
            #pragma target 4.0
            #pragma vertex vert
            #pragma geometry geom
            #pragma fragment fragBody
            ENDCG
        }

        Pass
        {
            Name "World Block Glow"
            Blend SrcAlpha One
            Cull Off
            ZWrite Off
            ZTest LEqual

            CGPROGRAM
            #pragma target 4.0
            #pragma vertex vert
            #pragma geometry geom
            #pragma fragment fragGlow
            ENDCG
        }
    }

    Fallback "Unlit/Transparent"
}
