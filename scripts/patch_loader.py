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
    "            MelonAssemblyResolver.Setup();",
    """            MelonAssemblyResolver.Setup();
            MelonLogger.MsgDirect("[trace] assembly resolver done"); MelonLogger.Flush();""")

sub("MelonLoader/Core.cs",
    """            Fixes.DotnetAssemblyLoadContextFix.Install();
            Fixes.DotnetModHandlerRedirectionFix.Install();""",
    """            Fixes.DotnetAssemblyLoadContextFix.Install();
            MelonLogger.MsgDirect("[trace] loadcontext fix done"); MelonLogger.Flush();
            Fixes.DotnetModHandlerRedirectionFix.Install();
            MelonLogger.MsgDirect("[trace] mod handler redirect done"); MelonLogger.Flush();""")

sub("MelonLoader/Core.cs",
    """            Fixes.ForcedCultureInfo.Install();
            Fixes.InstancePatchFix.Install();
            Fixes.ProcessFix.Install();""",
    """            Fixes.ForcedCultureInfo.Install();
            Fixes.InstancePatchFix.Install();
            Fixes.ProcessFix.Install();
            MelonLogger.MsgDirect("[trace] basic fixes done"); MelonLogger.Flush();""")

sub("MelonLoader/Core.cs",
    "            Fixes.Il2CppInteropFixes.Install();",
    """            MelonLogger.MsgDirect("[trace] Il2CppInteropFixes.Install begin"); MelonLogger.Flush();
            Fixes.Il2CppInteropFixes.Install();
            MelonLogger.MsgDirect("[trace] Il2CppInteropFixes.Install done"); MelonLogger.Flush();""")

sub("MelonLoader/Core.cs",
    "            Fixes.Il2CppICallInjector.Install();",
    """            Fixes.Il2CppICallInjector.Install();
            MelonLogger.MsgDirect("[trace] ICall injector done"); MelonLogger.Flush();""")

sub("MelonLoader/Core.cs",
    "            PatchShield.Install();",
    """            PatchShield.Install();
            MelonLogger.MsgDirect("[trace] patch shield done"); MelonLogger.Flush();""")

sub("MelonLoader/Core.cs",
    "            MelonPreferences.Load();",
    """            MelonPreferences.Load();
            MelonLogger.MsgDirect("[trace] preferences loaded"); MelonLogger.Flush();""")

sub("MelonLoader/Core.cs",
    "            MelonCompatibilityLayer.LoadModules();",
    """            MelonCompatibilityLayer.LoadModules();
            MelonLogger.MsgDirect("[trace] compat layers loaded"); MelonLogger.Flush();""")

sub("MelonLoader/Core.cs",
    """            MelonHandler.LoadUserlibs(MelonEnvironment.UserLibsDirectory);
            MelonHandler.LoadMelonFolders<MelonPlugin>(MelonEnvironment.PluginsDirectory);""",
    """            MelonLogger.MsgDirect("[trace] loading userlibs"); MelonLogger.Flush();
            MelonHandler.LoadUserlibs(MelonEnvironment.UserLibsDirectory);
            MelonLogger.MsgDirect("[trace] loading plugins"); MelonLogger.Flush();
            MelonHandler.LoadMelonFolders<MelonPlugin>(MelonEnvironment.PluginsDirectory);
            MelonLogger.MsgDirect("[trace] plugins loaded"); MelonLogger.Flush();""")

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
            try
            {
                if (_success)
                    _success = Il2CppAssemblyGenerator.Run();
            }
            catch (Exception ex)
            {
                MelonLogger.MsgDirect($"[trace] Il2CppAssemblyGenerator EXCEPTION: {ex.GetType().Name}: {ex.Message}"); MelonLogger.Flush();
                _success = false;
            }
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

# ------------------------------------------------------- SupportModule.cs
# Without the il2cpp support module nothing delivers Unity callbacks (OnUpdate/OnGUI)
# to mods, so the Mod Helper UI never appears. Its failure is swallowed by
# MelonDebug.Error unless debug logging was requested on the command line, which
# we cannot do on Android - make it loud instead.
sub("MelonLoader/SupportModule/SupportModule.cs",
    """                catch (Exception ex)
                {
                    MelonDebug.Error($"Support Module [{enumerator.Current.FileName}] threw an Exception: {ex}");
                    continue;
                }""",
    """                catch (Exception ex)
                {
                    MelonLogger.MsgDirect($"[trace] Support Module [{enumerator.Current.FileName}] EXCEPTION: {ex}"); MelonLogger.Flush();
                    continue;
                }""")

sub("MelonLoader/SupportModule/SupportModule.cs",
    """        internal static bool Setup()
        {
            BaseDirectory = MelonEnvironment.SupportModuleDirectory;""",
    """        internal static bool Setup()
        {
            BaseDirectory = MelonEnvironment.SupportModuleDirectory;
            MelonLogger.MsgDirect($"[trace] SupportModule.Setup dir='{BaseDirectory}'"); MelonLogger.Flush();""")

# ------------------------------------------------------- support module
# The il2cpp support module (Il2Cpp.dll) is where the process dies on Unity 6000.3,
# and the only diagnostics we get are whatever it prints, so trace every step.
sub("Dependencies/SupportModules/Il2Cpp/Main.cs",
    """            }).AddLogger(new InteropLogger())
              .AddHarmonySupport();""",
    """            }).AddLogger(new InteropLogger())
              .AddHarmonySupport();

            MelonLogger.MsgDirect("[trace] support: interop runtime created"); MelonLogger.Flush();""")

sub("Dependencies/SupportModules/Il2Cpp/Main.cs",
    """            SceneHandler.Init();

            MonoEnumeratorWrapper.Register();

            ClassInjector.RegisterTypeInIl2Cpp<SM_Component>();
            SM_Component.Create();

            Interop = new InteropInterface();
            Interface.SetInteropSupportInterface(Interop);
            runtime.Start();""",
    """            SceneHandler.Init();
            MelonLogger.MsgDirect("[trace] support: scene handler installed"); MelonLogger.Flush();

            MonoEnumeratorWrapper.Register();
            MelonLogger.MsgDirect("[trace] support: enumerator wrapper registered"); MelonLogger.Flush();

            ClassInjector.RegisterTypeInIl2Cpp<SM_Component>();
            MelonLogger.MsgDirect("[trace] support: SM_Component registered"); MelonLogger.Flush();
            SM_Component.Create();
            MelonLogger.MsgDirect("[trace] support: component created"); MelonLogger.Flush();

            Interop = new InteropInterface();
            Interface.SetInteropSupportInterface(Interop);
            MelonLogger.MsgDirect("[trace] support: interop interface set"); MelonLogger.Flush();
            runtime.Start();
            MelonLogger.MsgDirect("[trace] support: runtime started"); MelonLogger.Flush();""")

# --------------------------------------------------- Il2CppInterop (vendored)
# RegisterTypeOptions.LogSuccess used to be a plain setter. MonoMod re-emits the
# Harmony wrappers with a call to the plain accessor, so an `init` accessor makes
# every patch below it fail with MissingMethodException.
sub("External/Il2CppInterop/Il2CppInterop.Runtime/Injection/ClassInjector.cs",
    "    public bool LogSuccess { get; init; } = true;",
    "    public bool LogSuccess { get; set; } = true;")

# Injected classes are addressed with negative "type definition indexes" and that
# only works when this function is hooked. On Unity 6000.3 the xref walk in the
# finder no longer lands on it (il2cpp_image_get_class has an extra call), so
# without the fallback below il2cpp dereferences a negative index and the process
# dies right after the first injected type is registered.
sub("External/Il2CppInterop/Il2CppInterop.Runtime/Injection/Hooks/MetadataCache_GetTypeInfoFromTypeDefinitionIndex_Hook.cs",
    """        public override IntPtr FindTargetMethod()
        {
            return FindGetTypeInfoFromTypeDefinitionIndex();
        }""",
    """        public override IntPtr FindTargetMethod()
        {
            IntPtr found = FindGetTypeInfoFromTypeDefinitionIndex();
            if (found != IntPtr.Zero)
                return found;

            return ScanForTarget();
        }

        private static unsafe IntPtr ScanForTarget()
        {
            var module = InjectorHelpers.Il2CppModule;
            if (module == null)
                return IntPtr.Zero;

            byte* imageBase = (byte*)module.BaseAddress;
            int imageSize = module.ModuleMemorySize;
            if (imageSize < 0x1000)
                return IntPtr.Zero;

            // ELF64 program headers tell us which parts of the image are executable.
            if (*(uint*)imageBase != 0x464C457Fu)
                return IntPtr.Zero;

            ulong phoff = *(ulong*)(imageBase + 0x20);
            ushort phentsize = *(ushort*)(imageBase + 0x36);
            ushort phnum = *(ushort*)(imageBase + 0x38);

            for (int i = 0; i < phnum; i++)
            {
                byte* ph = imageBase + phoff + (ulong)i * phentsize;
                if (*(uint*)ph != 1u) // PT_LOAD
                    continue;
                if ((*(uint*)(ph + 4) & 1u) == 0) // PF_X
                    continue;

                ulong vaddr = *(ulong*)(ph + 0x10);
                ulong filesz = *(ulong*)(ph + 0x20);
                if (filesz == 0 || filesz > int.MaxValue)
                    continue;

                byte* segStart = imageBase + vaddr;
                if ((byte*)module.BaseAddress + imageSize <= segStart)
                    continue;

                IntPtr hit = ScanSegment(segStart, (int)filesz);
                if (hit != IntPtr.Zero)
                    return hit;
            }

            return IntPtr.Zero;
        }

        private static unsafe IntPtr ScanSegment(byte* start, int length)
        {
            // MetadataCache::GetTypeInfoFromTypeDefinitionIndex starts with
            //     if (index == -1) return ...;
            //     Il2CppClass* klass = typeInfoCache[index];  // dmb ishld, fill under lock
            // so look for `cmn w0, #1`, a conditional branch, the cached array load
            // (indexed by w0, scaled by 8) and the load barrier right after it.
            var span = new ReadOnlySpan<byte>(start, length);
            var needle = BitConverter.GetBytes(0x3100041Fu); // cmn w0, #1
            int offset = 0;
            while (offset < length - 64)
            {
                int rel = span.Slice(offset).IndexOf(needle);
                if (rel < 0)
                    break;

                int pos = offset + rel;
                offset = pos + 1;
                if ((pos & 3) != 0 || pos < 48)
                    continue;

                uint* words = (uint*)(start + pos);

                if ((words[1] & 0xFF000010u) != 0x54000000u) // b.cond
                    continue;
                if ((words[5] & 0xFFE0FC00u) != 0xF860D800u) // ldr xN, [xM, ..., sxtw #3]
                    continue;
                if (((words[5] >> 16) & 0x1Fu) != 0u) // index register is w0
                    continue;
                if (words[6] != 0xD50339BFu) // dmb ishld
                    continue;

                for (int back = 5; back <= 9; back++)
                {
                    if ((words[-back] & 0xFF8003FFu) != 0xD10003FFu) // sub sp, sp, #imm
                        continue;

                    var candidate = (IntPtr)(start + pos - back * 4);
                    Logger.Instance.LogInformation(
                        "Found MetadataCache::GetTypeInfoFromTypeDefinitionIndex by signature at 0x{Addr}",
                        candidate.ToInt64().ToString("X2"));
                    return candidate;
                }
            }

            return IntPtr.Zero;
        }""")

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

# The AssetsTools.NET- based parser stalls forever on Unity 6000 (APKAssetStream is
# not seekable and LoadClassDatabaseFromPackage never returns for 6000.3).
# Only the engine version really matters, and it is a plain header string.
sub("MelonLoader/InternalUtils/UnityInformationHandler.cs",
    """        private static void ReadGameInfo(AssetsManager assetsManager, string gameDataPath)
        {
            AssetsFileInstance instance = null;
            try
            {
                string bundlePath = Path.Combine(gameDataPath, "globalgamemanagers");
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
                }

                if (instance == null)
                    return;

                assetsManager.LoadIncludedClassPackage();
                if (!instance.file.Metadata.TypeTreeEnabled)
                    assetsManager.LoadClassDatabaseFromPackage(instance.file.Metadata.UnityVersion);

                if (EngineVersion == UnityVersion.MinVersion)
                    EngineVersion = TryParse(instance.file.Metadata.UnityVersion);

                List<AssetFileInfo> assetFiles = instance.file.GetAssetsOfType(AssetClassID.PlayerSettings);
                if (assetFiles.Count > 0)
                {
                    AssetFileInfo playerSettings = assetFiles.First();

                    AssetTypeValueField playerSettings_baseField = assetsManager.GetBaseField(instance, playerSettings);
                    if (playerSettings_baseField != null)
                    {
                        AssetTypeValueField bundleVersion = playerSettings_baseField.Get("bundleVersion");
                        if (bundleVersion != null)
                            GameVersion = bundleVersion.AsString;

                        AssetTypeValueField companyName = playerSettings_baseField.Get("companyName");
                        if (companyName != null)
                            GameDeveloper = companyName.AsString;

                        AssetTypeValueField productName = playerSettings_baseField.Get("productName");
                        if (productName != null)
                            GameName = productName.AsString;
                    }
                }
            }
            catch (Exception ex)
            {
                if (MelonDebug.IsEnabled())
                    MelonLogger.Error(ex);
            }
            if (instance != null)
                instance.file.Close();
        }""",
    """        private static void ReadGameInfo(AssetsManager assetsManager, string gameDataPath)
        {
            // Android fork: AssetsTools.NET deadlocks on Unity 6000 asset files read
            // through APKAssetStream. We only need the engine version, which sits as a
            // plain null-terminated string in the globalgamemanagers header.
            string ggmPath = Path.Combine(gameDataPath, "globalgamemanagers");
            try
            {
                if (!APKAssetManager.DoesAssetExist(ggmPath))
                {
                    MelonLogger.MsgDirect("[trace] RGI no globalgamemanagers, skipping"); MelonLogger.Flush();
                    return;
                }

                byte[] ggm = APKAssetManager.GetAssetBytes(ggmPath);
                MelonLogger.MsgDirect($"[trace] RGI globalgamemanagers bytes={ggm.Length}"); MelonLogger.Flush();

                if (ggm == null || ggm.Length < 0x40)
                    return;

                UnityVersion parsed = GetVersionFromGlobalGameManagers(ggm);
                MelonLogger.MsgDirect($"[trace] RGI parsed unity version '{parsed}'"); MelonLogger.Flush();

                if (parsed != UnityVersion.MinVersion)
                    EngineVersion = parsed;

                GameName = BootstrapInterop.NativeGetPackageName();
                if (string.IsNullOrEmpty(GameName))
                    GameName = "UNKNOWN";
                if (string.IsNullOrEmpty(GameDeveloper))
                    GameDeveloper = "UNKNOWN";
            }
            catch (Exception ex)
            {
                MelonLogger.MsgDirect($"[trace] RGI EXCEPTION: {ex.GetType().Name}: {ex.Message}"); MelonLogger.Flush();
                MelonDebug.Msg(ex.ToString());
            }
        }""")

print("all patches applied")
