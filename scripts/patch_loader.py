#!/usr/bin/env python3
"""Applies BTD6/Android fixes + tracing to the LemonLoader MelonLoader sources.

Run from the root of the MelonLoader checkout (the `ll/` folder in CI).
Every edit is an exact string replacement with an assert, so a silent
"patch applied to nothing" is impossible.
"""
import io
import os
import sys

def rd(path):
    return io.open(path, encoding="utf-8-sig").read()

def wr(path, text):
    io.open(path, "w", encoding="utf-8").write(text)

def sub(path, old, new, count=1):
    text = rd(path)
    found = text.count(old)
    if found < count:
        sys.exit("!! %s: pattern not found (%d/%d):\n%s" % (path, found, count, old))
    wr(path, text.replace(old, new, count))
    print("patched %s (%d)" % (path, count))

# ---------------------------------------------------------------- csproj
sub("MelonLoader/MelonLoader.csproj",
    '<PackageReference Include="AsmResolver.DotNet" Version="6.0.0-beta.2" />',
    '<PackageReference Include="AsmResolver.DotNet" Version="6.0.0-beta.5" />')

# ------------------------------------------------- Il2CppInteropFixes
# AsmResolver 6.0.0-beta.5: TypeDefinition.Module -> DeclaringModule
sub("MelonLoader/Fixes/Il2CppInteropFixes.cs",
    """                || (__0.Module == null)
                || (__0.Module.Assembly == null)""",
    """                || (__0.DeclaringModule == null)
                || (__0.DeclaringModule.Assembly == null)""")
sub("MelonLoader/Fixes/Il2CppInteropFixes.cs",
    "            string assemblyName = __0.Module.Assembly.Name;",
    "            string assemblyName = __0.DeclaringModule.Assembly.Name;")

# ------------------------------------------------------------ Core.cs
sub("MelonLoader/Core.cs",
    "            MelonEnvironment.PackageName = BootstrapInterop.NativeGetPackageName();",
    """            MelonEnvironment.PackageName = BootstrapInterop.NativeGetPackageName();

            // heartbeat: tells us later whether the process died or just hung
            try
            {
                var hbPath = Path.Combine(MelonEnvironment.GameRootDirectory, "hb.txt");
                new Thread(() =>
                {
                    while (true)
                    {
                        try { File.AppendAllText(hbPath, "x"); } catch { }
                        Thread.Sleep(500);
                    }
                }) { IsBackground = true }.Start();
            }
            catch { }""")

sub("MelonLoader/Core.cs",
    "            APKAssetManager.CopyAdditionalData();",
    """            MelonLogger.MsgDirect("[trace] copyAdditionalData begin"); MelonLogger.Flush();
            APKAssetManager.CopyAdditionalData();
            MelonLogger.MsgDirect("[trace] copyAdditionalData done"); MelonLogger.Flush();""")

sub("MelonLoader/Core.cs",
    "            MelonUtils.Setup(AppDomain.CurrentDomain);",
    """            MelonLogger.MsgDirect("[trace] MelonUtils.Setup begin"); MelonLogger.Flush();
            MelonUtils.Setup(AppDomain.CurrentDomain);
            MelonLogger.MsgDirect("[trace] MelonUtils.Setup done"); MelonLogger.Flush();""")

sub("MelonLoader/Core.cs",
    "            Fixes.Il2CppInteropFixes.Install();",
    """            MelonLogger.MsgDirect("[trace] Il2CppInteropFixes.Install begin"); MelonLogger.Flush();
            Fixes.Il2CppInteropFixes.Install();
            MelonLogger.MsgDirect("[trace] Il2CppInteropFixes.Install done"); MelonLogger.Flush();""")

sub("MelonLoader/Core.cs",
    """            MelonEvents.MelonHarmonyEarlyInit.Invoke();
            MelonEvents.OnPreInitialization.Invoke();

            return 0;""",
    """            MelonLogger.MsgDirect("[trace] Initialize finished"); MelonLogger.Flush();
            MelonEvents.MelonHarmonyEarlyInit.Invoke();
            MelonEvents.OnPreInitialization.Invoke();
            MelonLogger.MsgDirect("[trace] pre-init events done"); MelonLogger.Flush();

            return 0;""")

sub("MelonLoader/Core.cs",
    """            if (_success)
                _success = Il2CppAssemblyGenerator.Run();""",
    """            MelonLogger.MsgDirect("[trace] Il2CppAssemblyGenerator.Run begin"); MelonLogger.Flush();
            if (_success)
                _success = Il2CppAssemblyGenerator.Run();
            MelonLogger.MsgDirect($"[trace] Il2CppAssemblyGenerator.Run done, success={_success}"); MelonLogger.Flush();""")

# --------------------------------------------------------- MelonUtils.cs
sub("MelonLoader/MelonUtils.cs",
    "            Core.WelcomeMessage();",
    """            MelonLogger.MsgDirect("[trace] welcome message begin"); MelonLogger.Flush();
            Core.WelcomeMessage();
            MelonLogger.MsgDirect("[trace] welcome message done"); MelonLogger.Flush();""")

sub("MelonLoader/MelonUtils.cs",
    "            MelonHandler.Setup();",
    """            MelonHandler.Setup();
            MelonLogger.MsgDirect("[trace] MelonHandler.Setup done"); MelonLogger.Flush();""")

sub("MelonLoader/MelonUtils.cs",
    "            UnityInformationHandler.Setup();",
    """            UnityInformationHandler.Setup();
            MelonLogger.MsgDirect("[trace] UnityInformationHandler.Setup done"); MelonLogger.Flush();""")

# ------------------------------------------------------ APKAssetManager
sub("MelonLoader/Utils/APKAssetManager.cs",
    """        JObjectArray<JString> assets = JNI.CallObjectMethod<JObjectArray<JString>>(assetManager, JNI.GetMethodID(JNI.GetObjectClass(assetManager), "list", "(Ljava/lang/String;)[Ljava/lang/String;"), new JValue(pathString));

        string[] cleanAssets = assets.Select(a => a.GetString()).ToArray();
        HandleException();

        return cleanAssets;""",
    """        JObjectArray<JString> assets = JNI.CallObjectMethod<JObjectArray<JString>>(assetManager, JNI.GetMethodID(JNI.GetObjectClass(assetManager), "list", "(Ljava/lang/String;)[Ljava/lang/String;"), new JValue(pathString));

        // a pending Java exception left uncleared here poisons every later JNI call
        if (JNI.ExceptionCheck())
        {
            MelonLogger.MsgDirect($"[trace] asset list threw for '{directory}'"); MelonLogger.Flush();
            JNI.ExceptionClear();
            return new string[0];
        }

        if (assets == null)
        {
            MelonLogger.MsgDirect($"[trace] asset list null for '{directory}'"); MelonLogger.Flush();
            return new string[0];
        }

        string[] cleanAssets = assets.Select(a => a.GetString()).ToArray();
        HandleException();

        return cleanAssets;""")

sub("MelonLoader/Utils/APKAssetManager.cs",
    """        // using `list` isn't as fast as just calling open, but this allows the function to not crash on debuggable builds of apps
        string containingDir = path[..path.LastIndexOf('/')];
        JString pathString = JNI.NewString(containingDir);
        JObjectArray<JString> assets = JNI.CallObjectMethod<JObjectArray<JString>>(assetManager, JNI.GetMethodID(JNI.GetObjectClass(assetManager), "list", "(Ljava/lang/String;)[Ljava/lang/String;"), new JValue(pathString));

        bool exists = assets.Any(js =>
        {
            string asset = JNI.GetJStringString(js);
            return path.EndsWith(asset);
        });

        HandleException();

        return exists;""",
    """        // using `list` isn't as fast as just calling open, but this allows the function to not crash on debuggable builds of apps
        int slash = path.LastIndexOf('/');
        if (slash < 0)
            return false;

        string containingDir = path[..slash];
        string fileName = path[(slash + 1)..];

        string[] assets = GetDirectoryContents(containingDir);
        bool exists = false;
        for (int i = 0; i < assets.Length; i++)
            if (assets[i] == fileName)
                exists = true;

        MelonLogger.MsgDirect($"[trace] asset '{path}' exists={exists} (dir entries: {assets.Length})"); MelonLogger.Flush();

        return exists;""")

sub("MelonLoader/Utils/APKAssetManager.cs",
    """        if (asset == null || !asset.Valid())
            return null;

        HandleException();

        return new APKAssetStream(asset);""",
    """        if (asset == null || !asset.Valid())
        {
            MelonLogger.MsgDirect($"[trace] asset open failed: '{path}'"); MelonLogger.Flush();
            HandleException();
            return null;
        }

        HandleException();

        return new APKAssetStream(asset);""")

# -------------------------------------------------- UnityInformationHandler
sub("MelonLoader/InternalUtils/UnityInformationHandler.cs",
    """        internal static void Setup()
        {
            string gameDataPath = MelonEnvironment.UnityGameDataDirectory;""",
    """        internal static void Setup()
        {
            try
            {
                SetupInternal();
            }
            catch (Exception ex)
            {
                MelonLogger.MsgDirect($"[trace] UnityInformationHandler.Setup EXCEPTION: {ex.GetType().Name}: {ex.Message}"); MelonLogger.Flush();
            }
        }

        private static void SetupInternal()
        {
            string gameDataPath = MelonEnvironment.UnityGameDataDirectory;
            MelonLogger.MsgDirect($"[trace] gameDataPath='{gameDataPath}'"); MelonLogger.Flush();""")

sub("MelonLoader/InternalUtils/UnityInformationHandler.cs",
    """                string bundlePath = Path.Combine(gameDataPath, "globalgamemanagers");
                if (!APKAssetManager.DoesAssetExist(bundlePath))
                    bundlePath = Path.Combine(gameDataPath, "mainData");

                if (!APKAssetManager.DoesAssetExist(bundlePath))
                {
                    bundlePath = Path.Combine(gameDataPath, "data.unity3d");
                    if (!APKAssetManager.DoesAssetExist(bundlePath))
                        return;

                    Stream bundleStream = APKAssetManager.GetAssetStream(bundlePath);
                    BundleFileInstance bundleFile = assetsManager.LoadBundleFile(bundleStream, bundlePath);
                    instance = assetsManager.LoadAssetsFileFromBundle(bundleFile, "globalgamemanagers");
                }
                else
                {
                    Stream bundleStream = APKAssetManager.GetAssetStream(bundlePath);
                    instance = assetsManager.LoadAssetsFile(bundleStream, bundlePath, true);
                }""",
    """                string bundlePath = Path.Combine(gameDataPath, "globalgamemanagers");

                if (APKAssetManager.DoesAssetExist(bundlePath))
                {
                    MelonLogger.MsgDirect("[trace] RGI opening globalgamemanagers"); MelonLogger.Flush();
                    Stream ggmStream = APKAssetManager.GetAssetStream(bundlePath);
                    instance = assetsManager.LoadAssetsFile(ggmStream, bundlePath, true);
                    MelonLogger.MsgDirect("[trace] RGI globalgamemanagers loaded"); MelonLogger.Flush();
                }
                else
                {
                    bundlePath = Path.Combine(gameDataPath, "mainData");
                    if (APKAssetManager.DoesAssetExist(bundlePath))
                    {
                        MelonLogger.MsgDirect("[trace] RGI opening mainData"); MelonLogger.Flush();
                        Stream mainStream = APKAssetManager.GetAssetStream(bundlePath);
                        instance = assetsManager.LoadAssetsFile(mainStream, bundlePath, true);
                        MelonLogger.MsgDirect("[trace] RGI mainData loaded"); MelonLogger.Flush();
                    }
                    else
                    {
                        bundlePath = Path.Combine(gameDataPath, "data.unity3d");
                        if (!APKAssetManager.DoesAssetExist(bundlePath))
                        {
                            MelonLogger.MsgDirect("[trace] RGI no usable asset file, giving up"); MelonLogger.Flush();
                            return;
                        }

                        MelonLogger.MsgDirect("[trace] RGI opening data.unity3d"); MelonLogger.Flush();
                        Stream bundleStream = APKAssetManager.GetAssetStream(bundlePath);
                        BundleFileInstance bundleFile = assetsManager.LoadBundleFile(bundleStream, bundlePath);
                        MelonLogger.MsgDirect("[trace] RGI bundle loaded"); MelonLogger.Flush();
                        instance = assetsManager.LoadAssetsFileFromBundle(bundleFile, "globalgamemanagers");
                        MelonLogger.MsgDirect("[trace] RGI bundle assets loaded"); MelonLogger.Flush();
                    }
                }""")

sub("MelonLoader/InternalUtils/UnityInformationHandler.cs",
    """                assetsManager.LoadIncludedClassPackage();""",
    """                MelonLogger.MsgDirect("[trace] RGI LoadIncludedClassPackage begin"); MelonLogger.Flush();
                assetsManager.LoadIncludedClassPackage();
                MelonLogger.MsgDirect("[trace] RGI LoadIncludedClassPackage done"); MelonLogger.Flush();""")

sub("MelonLoader/InternalUtils/UnityInformationHandler.cs",
    """            catch (Exception ex)
            {
                if (MelonDebug.IsEnabled())
                    MelonLogger.Error(ex);
            }
            if (instance != null)
                instance.file.Close();""",
    """            catch (Exception ex)
            {
                MelonLogger.MsgDirect($"[trace] RGI EXCEPTION: {ex.GetType().Name}: {ex.Message}"); MelonLogger.Flush();
                MelonDebug.Msg(ex.ToString());
            }
            if (instance != null)
                instance.file.Close();""")

print("all patches applied")
