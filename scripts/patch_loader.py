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
            // Process.Modules is unreliable here: on Android the reported base of
            // libil2cpp.so can point into the middle of the image, so read
            // /proc/self/maps and scan the executable mappings of the library as-is.
            string fileName = null;
            try
            {
                var module = InjectorHelpers.Il2CppModule;
                if (module != null)
                    fileName = module.FileName;
            }
            catch
            {
            }

            if (string.IsNullOrEmpty(fileName))
                fileName = "libil2cpp.so";
            else
                fileName = System.IO.Path.GetFileName(fileName);

            int mappings = 0;
            try
            {
                foreach (string line in System.IO.File.ReadAllLines("/proc/self/maps"))
                {
                    int space = line.IndexOf(' ');
                    if (space < 8 || space + 4 >= line.Length)
                        continue;

                    string range = line.Substring(0, space);
                    int dash = range.IndexOf('-');
                    if (dash < 0)
                        continue;

                    if (line[space + 3] != 'x') // r-xp / --xp
                        continue;

                    if (!line.Contains(fileName))
                        continue;

                    ulong start, end;
                    try
                    {
                        start = Convert.ToUInt64(range.Substring(0, dash), 16);
                        end = Convert.ToUInt64(range.Substring(dash + 1), 16);
                    }
                    catch
                    {
                        continue;
                    }

                    ulong length = end - start;
                    if (length < 0x1000 || length > int.MaxValue)
                        continue;

                    mappings++;
                    Logger.Instance.LogInformation("Signature scan: mapping 0x{Start} size 0x{Length}",
                        start.ToString("X2"), length.ToString("X2"));

                    IntPtr hit = ScanSegment((byte*)start, (int)length);
                    if (hit != IntPtr.Zero)
                        return hit;
                }
            }
            catch (Exception ex)
            {
                Logger.Instance.LogWarning($"Signature scan failed: {ex}");
                return IntPtr.Zero;
            }

            if (mappings == 0)
                Logger.Instance.LogWarning("Signature scan: no executable mappings found for {File}", fileName);

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

# Delegate conversion without il2cpp reflection: on Unity 6000 metadata
# Il2CppSystem.Reflection.MethodInfo.GetParameters() dies with a native fault (no
# managed exception), so the native Invoke metadata is read through the il2cpp C
# API and the trampoline signature is keyed by the native method pointer.
sub("External/Il2CppInterop/Il2CppInterop.Runtime/DelegateSupport.cs",
    """        var il2CppDelegateType = Il2CppSystem.Type.internal_from_handle(IL2CPP.il2cpp_class_get_type(classTypePtr));
        var nativeDelegateInvokeMethod = il2CppDelegateType.GetMethod("Invoke");

        var nativeParameters = nativeDelegateInvokeMethod.GetParameters();
        if (nativeParameters.Count != parameterInfos.Length)
            throw new ArgumentException(
                $"Managed delegate has {parameterInfos.Length} parameters, native has {nativeParameters.Count}, these should match");

        for (var i = 0; i < nativeParameters.Count; i++)
        {
            var nativeType = nativeParameters[i].ParameterType;
            var managedType = parameterInfos[i].ParameterType;

            if (nativeType.IsPrimitive || managedType.IsPrimitive)
            {
                if (nativeType.FullName != managedType.FullName)
                    throw new ArgumentException(
                        $"Parameter type mismatch at parameter {i}: {nativeType.FullName} != {managedType.FullName}");

                continue;
            }

            var classPointerFromManagedType = (IntPtr)typeof(Il2CppClassPointerStore<>).MakeGenericType(managedType)
                .GetField(nameof(Il2CppClassPointerStore<int>.NativeClassPtr)).GetValue(null);

            var classPointerFromNativeType = IL2CPP.il2cpp_class_from_type(nativeType._impl.value);

            if (classPointerFromManagedType != classPointerFromNativeType)
                throw new ArgumentException(
                    $"Parameter type at {i} has mismatched native type pointers; types: {nativeType.FullName} != {managedType.FullName}");

            if (nativeType.IsByRef || managedType.IsByRef)
                throw new ArgumentException($"Parameter at {i} is passed by reference, this is not supported");
        }

        var signature = new MethodSignature(nativeDelegateInvokeMethod, true);
        var managedTrampoline =
            GetOrCreateNativeToManagedTrampoline(signature, nativeDelegateInvokeMethod, managedInvokeMethod);

        var methodInfo = UnityVersionHandler.NewMethod();
        methodInfo.MethodPointer = Marshal.GetFunctionPointerForDelegate(managedTrampoline);
        methodInfo.ParametersCount = (byte)parameterInfos.Length;
        methodInfo.Slot = ushort.MaxValue;
        methodInfo.IsMarshalledFromNative = true;

        var delegateReference = new Il2CppToMonoDelegateReference(@delegate, methodInfo.Pointer);
""",
    """        Logger.Instance.LogInformation("convert: {Type} class=0x{Class} native=0x{Native}",
            typeof(TIl2Cpp).FullName, classTypePtr.ToInt64().ToString("X2"),
            IL2CPP.il2cpp_class_get_type(classTypePtr).ToInt64().ToString("X2"));

        var nativeDelegateInvokeMethod = FindNativeInvokeMethod(classTypePtr, parameterInfos.Length);
        Logger.Instance.LogInformation("convert: {Type} native Invoke method=0x{Method}",
            typeof(TIl2Cpp).FullName, nativeDelegateInvokeMethod.ToInt64().ToString("X2"));
        if (nativeDelegateInvokeMethod == IntPtr.Zero)
            throw new ArgumentException(
                $"Type {typeof(TIl2Cpp)} has no il2cpp Invoke method with {parameterInfos.Length} parameters");

        var nativeParameterCount = (int)IL2CPP.il2cpp_method_get_param_count(nativeDelegateInvokeMethod);
        Logger.Instance.LogInformation("convert: {Type} native parameters count={Count}",
            typeof(TIl2Cpp).FullName, nativeParameterCount);
        if (nativeParameterCount != parameterInfos.Length)
            throw new ArgumentException(
                $"Managed delegate has {parameterInfos.Length} parameters, native has {nativeParameterCount}, these should match");

        for (var i = 0; i < nativeParameterCount; i++)
        {
            var managedType = parameterInfos[i].ParameterType;
            if (managedType.IsByRef)
                throw new ArgumentException($"Parameter at {i} is passed by reference, this is not supported");

            var classPointerFromNativeType =
                IL2CPP.il2cpp_class_from_type(IL2CPP.il2cpp_method_get_param(nativeDelegateInvokeMethod, (uint)i));
            var classPointerFromManagedType = Il2CppClassPointerStore.GetNativeClassPointer(managedType);

            Logger.Instance.LogInformation(
                "convert: {Type} param {I} managed={M} managedClass=0x{MC} nativeClass=0x{NC}",
                typeof(TIl2Cpp).FullName, i, managedType.FullName,
                classPointerFromManagedType.ToInt64().ToString("X2"),
                classPointerFromNativeType.ToInt64().ToString("X2"));

            // Managed-only types (Scene, plain structs from the Unity assemblies)
            // have no il2cpp class of their own; the trampoline keeps their layout.
            if ((classPointerFromManagedType != IntPtr.Zero) &&
                (classPointerFromManagedType != classPointerFromNativeType))
                throw new ArgumentException(
                    $"Parameter type at {i} has mismatched native type pointers; type: {managedType.FullName}");
        }

        Logger.Instance.LogInformation("convert: {Type} building signature", typeof(TIl2Cpp).FullName);
        var signature = new MethodSignature(nativeDelegateInvokeMethod);
        Logger.Instance.LogInformation("convert: {Type} generating trampoline", typeof(TIl2Cpp).FullName);
        var managedTrampoline =
            GetOrCreateNativeToManagedTrampoline(signature, nativeDelegateInvokeMethod, managedInvokeMethod);
        Logger.Instance.LogInformation("convert: {Type} trampoline ready", typeof(TIl2Cpp).FullName);

        var methodInfo = UnityVersionHandler.NewMethod();
        methodInfo.MethodPointer = Marshal.GetFunctionPointerForDelegate(managedTrampoline);
        methodInfo.ParametersCount = (byte)parameterInfos.Length;
        methodInfo.Slot = ushort.MaxValue;
        methodInfo.IsMarshalledFromNative = true;

        Logger.Instance.LogInformation("convert: {Type} instantiating native delegate", typeof(TIl2Cpp).FullName);
        var delegateReference = new Il2CppToMonoDelegateReference(@delegate, methodInfo.Pointer);
""")

# The il2cpp MethodInfo object cannot be built from here without going through
# the reflection code that crashes above, so the field is left at its default.
sub("External/Il2CppInterop/Il2CppInterop.Runtime/DelegateSupport.cs",
    """        converted.method_ptr = methodInfo.MethodPointer;
        converted.method_info = nativeDelegateInvokeMethod; // todo: is this truly a good hack?""",
    """        Logger.Instance.LogInformation("convert: {Type} done", typeof(TIl2Cpp).FullName);
        converted.method_ptr = methodInfo.MethodPointer;""")

# Native Invoke lookup (replaces il2cpp reflection) + pointer-keyed signatures.
sub("External/Il2CppInterop/Il2CppInterop.Runtime/DelegateSupport.cs",
    """    internal class MethodSignature : IEquatable<MethodSignature>""",
    """    private static IntPtr FindNativeInvokeMethod(IntPtr classPointer, int parameterCount)
    {
        var iterator = IntPtr.Zero;
        while (true)
        {
            var method = IL2CPP.il2cpp_class_get_methods(classPointer, ref iterator);
            if (method == IntPtr.Zero)
                return IntPtr.Zero;

            if (IL2CPP.il2cpp_method_get_name_(method) != "Invoke")
                continue;

            if ((int)IL2CPP.il2cpp_method_get_param_count(method) != parameterCount)
                continue;

            return method;
        }
    }

    internal class MethodSignature : IEquatable<MethodSignature>""")

sub("External/Il2CppInterop/Il2CppInterop.Runtime/DelegateSupport.cs",
    """        public MethodSignature(MethodInfo methodInfo, bool hasThis)""",
    """        public MethodSignature(IntPtr nativeMethodInfo)
        {
            HasThis = true;
            ConstructedFromNative = true;

            var hashCode = new HashCode();
            hashCode.Add(nativeMethodInfo.ToInt64());
            hashCode.Add(unchecked((int)IL2CPP.il2cpp_method_get_param_count(nativeMethodInfo)));
            _hashCode = hashCode.ToHashCode();
        }

        public MethodSignature(MethodInfo methodInfo, bool hasThis)""")

sub("External/Il2CppInterop/Il2CppInterop.Runtime/DelegateSupport.cs",
    """    private static Delegate GetOrCreateNativeToManagedTrampoline(MethodSignature signature,
        Il2CppSystem.Reflection.MethodInfo nativeMethod, MethodInfo managedMethod)""",
    """    private static Delegate GetOrCreateNativeToManagedTrampoline(MethodSignature signature,
        IntPtr nativeMethod, MethodInfo managedMethod)""")

sub("External/Il2CppInterop/Il2CppInterop.Runtime/DelegateSupport.cs",
    """    private static Delegate GenerateNativeToManagedTrampoline(Il2CppSystem.Reflection.MethodInfo nativeMethod,
        MethodInfo managedMethod, MethodSignature signature)""",
    """    private static Delegate GenerateNativeToManagedTrampoline(IntPtr nativeMethod,
        MethodInfo managedMethod, MethodSignature signature)""")

# nativeMethod is only used as a cache key now; its parameters used to be pulled
# through the crashing reflection call and were never used afterwards.
sub("External/Il2CppInterop/Il2CppInterop.Runtime/DelegateSupport.cs",
    """        var managedParameters = managedMethod.GetParameters();
        var nativeParameters = nativeMethod.GetParameters();
        var parameterTypes""",
    """        var managedParameters = managedMethod.GetParameters();
        var parameterTypes""")

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
