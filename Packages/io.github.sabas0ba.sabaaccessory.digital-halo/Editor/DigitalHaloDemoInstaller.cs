using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using PackageInfo = UnityEditor.PackageManager.PackageInfo;

namespace SabaAccessory.DigitalHalo.Editor
{
    public static class DigitalHaloDemoInstaller
    {
        private const string PackageName = "io.github.sabas0ba.sabaaccessory.digital-halo";
        private const string SampleName = "Digital Halo Demo";
        private const string SceneName = "DigitalHaloDemo.unity";

        [MenuItem("Tools/SabaAccessory/Digital Halo/Import and Open Demo Scene")]
        private static void ImportAndOpenFromMenu()
        {
            ImportAndOpen();
        }

        public static void ImportAndOpenForValidation()
        {
            ImportAndOpen();
        }

        private static void ImportAndOpen()
        {
            PackageInfo packageInfo = PackageInfo.FindForAssetPath("Packages/" + PackageName);
            if (packageInfo == null)
            {
                throw new InvalidOperationException("Digital Halo package information was not found.");
            }

            string destinationAssetPath = string.Join(
                "/",
                "Assets/Samples",
                packageInfo.displayName,
                packageInfo.version,
                SampleName
            );
            string sceneAssetPath = destinationAssetPath + "/" + SceneName;

            if (!AssetDatabase.IsValidFolder(destinationAssetPath))
            {
                string sourcePath = Path.Combine(packageInfo.resolvedPath, "Samples~", SampleName);
                if (!Directory.Exists(sourcePath))
                {
                    throw new DirectoryNotFoundException("Demo sample was not found: " + sourcePath);
                }

                string destinationPath = Path.GetFullPath(destinationAssetPath);
                string parentPath = Path.GetDirectoryName(destinationPath);
                if (string.IsNullOrEmpty(parentPath))
                {
                    throw new InvalidOperationException("Demo destination could not be resolved.");
                }

                Directory.CreateDirectory(parentPath);
                FileUtil.CopyFileOrDirectory(sourcePath, destinationPath);
                AssetDatabase.Refresh();
            }

            if (!File.Exists(Path.GetFullPath(sceneAssetPath)))
            {
                throw new FileNotFoundException("Demo scene was not imported.", sceneAssetPath);
            }

            if (
                !Application.isBatchMode
                && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()
            )
            {
                return;
            }

            EditorSceneManager.OpenScene(sceneAssetPath, OpenSceneMode.Single);
            Debug.Log("Opened Digital Halo demo scene: " + sceneAssetPath);
        }
    }
}
