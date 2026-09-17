[app]

title = School Helper
package.name = schoolhelper
package.domain = org.schoolhelper

source.dir = .

source.include_exts = py,json,png,jpg,jpeg,kv,atlas,ttf

version = 1.0.0

requirements = python3,kivy==2.3.1,https://github.com/kivymd/KivyMD/archive/master.zip,materialyoucolor==3.0.3,materialshapes,pycairo,pillow,exceptiongroup,asyncgui,asynckivy,android,plyer

orientation = portrait

fullscreen = 0

android.api = 35
android.minapi = 23

android.ndk = 28c
android.ndk_api = 23

android.archs = arm64-v8a

android.accept_sdk_license = True

android.private_storage = True

p4a.branch = master
p4a.commit = 58d2114

[buildozer]

log_level = 2
warn_on_root = 1
