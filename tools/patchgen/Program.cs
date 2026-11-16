// Replaces the body of a method with `return false;` (bool) / `return;` (void).
//
// We use it on MelonLoader's Il2CppAssemblyGenerator: `Core.TryDownloadPreGenerated`
// throws an AggregateException on any HTTP error (the LemonLoader fork wraps the
// 404 of its "pregenerated assemblies" CDN), which aborts generation before
// Cpp2IL ever runs. There is no pregenerated set for BTD6, so the whole check is
// useless to us -- and there is no way to rebuild the generator here (its
// Cpp2IL/Il2CppInterop submodules only build on a newer SDK), hence this hack.
using System;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;

internal static class Program
{
    private static int Main(string[] args)
    {
        if (args.Length < 3)
        {
            Console.Error.WriteLine("usage: patchgen <assembly.dll> <Full.Type.Name> <MethodName>");
            return 2;
        }

        string path = args[0];
        string typeName = args[1];
        string methodName = args[2];

        var resolver = new DefaultAssemblyResolver();
        resolver.AddSearchDirectory(System.IO.Path.GetDirectoryName(path));

        var assembly = AssemblyDefinition.ReadAssembly(path, new ReaderParameters
        {
            InMemory = true,
            ReadSymbols = false,
            AssemblyResolver = resolver,
        });

        var type = assembly.MainModule.GetType(typeName);
        if (type == null)
        {
            Console.Error.WriteLine($"type not found: {typeName}");
            return 1;
        }

        var method = type.Methods.FirstOrDefault(m => m.Name == methodName && m.HasBody);
        if (method == null)
        {
            Console.Error.WriteLine($"method not found: {typeName}::{methodName}");
            return 1;
        }

        string ret = method.ReturnType.FullName == "System.Void" ? "(void)" : method.ReturnType.FullName;

        var body = new MethodBody(method);
        var il = body.GetILProcessor();
        if (method.ReturnType.FullName != "System.Void")
            il.Emit(OpCodes.Ldc_I4_0);
        il.Emit(OpCodes.Ret);

        body.MaxStackSize = 8;
        method.Body = body;

        string tmp = path + ".tmp";
        assembly.Write(tmp, new WriterParameters { WriteSymbols = false });
        assembly.Dispose();

        System.IO.File.Move(tmp, path, true);
        Console.WriteLine($"patched {typeName}::{methodName} -> const {ret}");
        return 0;
    }
}
