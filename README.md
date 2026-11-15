# btd6-android-loader

Экспериментальный Android-форк загрузчика MelonLoader (база: LemonLoader 0.6.X),
цель — запустить моды BTD6 на телефоне.

## Проблема

LemonLoader 0.6.5 стартует в BTD6, но процесс умирает сразу после `Runtime Type: net8`:

```
Initialized JNI
------------------------------
MelonLoader v0.6.5 Open-Beta
OS: Android 12
Game Type: Il2cpp
Game Arch: x64
Runtime Type: net8     <-- дальше тишина
```

То же самое в LemonLoader issue #89 (открыт). Игра: BTD6, Unity 6000.3.23f1,
arm64, IL2CPP, Android 12.

## План

1. Собрать managed-часть MelonLoader 0.6.X в CI (dotnet на x64-раннере) — без NDK.
2. Трассировка в `Core.Initialize()` / `PreSetup()` — понять, на каком шаге умирает
   процесс (подозрение: `Il2CppInteropFixes.Install`).
3. Собрать `melon_data.zip`: нативные `.so` берём из релиза 0.6.5.1, managed — свои.
4. Патчить игру через «Patch with Local Unity Dependencies» нашим zip, смотреть лог.
5. Если 0.6.5 не лечится — перенести managed 0.7.3 (фиксы Unity 6000, Il2CppInterop 1.5.1)
   на нативную обвязку 0.6.5.

## Ограничения

- Нативные библиотеки на телефоне не собрать (NDK только под x86_64) → сборка в GitHub Actions.
- Источник: https://github.com/LemonLoader/MelonLoader, ветка 0.6.X.
