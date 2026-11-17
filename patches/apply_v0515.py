from pathlib import Path
import xml.etree.ElementTree as ET

root = Path("app/src/main")
manifest = root / "AndroidManifest.xml"
s = manifest.read_text(encoding="utf-8")
if 'android:icon=' not in s:
    s = s.replace('<application', '<application\n        android:icon="@drawable/ic_launcher"\n        android:roundIcon="@drawable/ic_launcher"')
manifest.write_text(s, encoding="utf-8")

drawable = root / "res/drawable"
drawable.mkdir(parents=True, exist_ok=True)
icon = """<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#08091A" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#32116F" android:pathData="M18,20h72v58h-72z"/>
    <path android:fillColor="#842BFF" android:pathData="M24,25h60v48h-60z"/>
    <path android:fillColor="#FFFFC86B" android:pathData="M35,14l7,8 12,-13 12,13 7,-8 -4,20h-30z"/>
    <path android:fillColor="#08091A" android:pathData="M26,39h55l-7,30h-35z"/>
    <path android:strokeColor="#FFFFC86B" android:strokeWidth="4" android:strokeLineCap="round" android:strokeLineJoin="round" android:fillColor="#00000000" android:pathData="M22,36h9l7,30h33l8,-23h-44"/>
    <path android:strokeColor="#FFFFC86B" android:strokeWidth="3" android:strokeLineCap="round" android:fillColor="#00000000" android:pathData="M43,44l3,18 M57,44v18 M70,44l-3,18"/>
    <path android:fillColor="#FFFFC86B" android:pathData="M42,72a5,5 0,1 0,10 0a5,5 0,1 0,-10 0 M66,72a5,5 0,1 0,10 0a5,5 0,1 0,-10 0"/>
    <path android:fillColor="#08091A" android:pathData="M68,63h25v25h-25z"/>
    <path android:strokeColor="#00D9FF" android:strokeWidth="4" android:fillColor="#00000000" android:pathData="M73,57a15,15 0,1 0,30 0a15,15 0,1 0,-30 0 M96,69l9,10"/>
    <path android:strokeColor="#00D9FF" android:strokeWidth="2.5" android:strokeLineCap="round" android:fillColor="#00000000" android:pathData="M88,47v20 M88,53l-6,-4 M88,58l6,-5 M88,62l-6,4 M88,62l6,4"/>
</vector>
"""
(drawable / "ic_launcher.xml").write_text(icon, encoding="utf-8")

gradle = Path("app/build.gradle")
g = gradle.read_text(encoding="utf-8")
g = g.replace("versionCode 20", "versionCode 21").replace("versionName '0.6.0'", "versionName '0.6.1'")
gradle.write_text(g, encoding="utf-8")
print("SMART BUY AI launcher icon and version 0.6.1 applied")
