[app]

title = School Helper
package.name = schoolhelper
package.domain = org.schoolhelper

source.dir = .

source.include_exts = py,json,png,jpg,jpeg,kv,atlas,ttf

version = 1.0.0

requirements = python3,kivy>=2.3.0,kivymd==2.0.0,plyer,materialyoucolor==3.0.3,materialshapes,pycairo,pillow,exceptiongroup,asyncgui,asynckivy,android

orientation = portrait

fullscreen = 0

android.permissions = INTERNET,POST_NOTIFICATIONS

android.api = 36
android.minapi = 23

android.ndk = 28c
android.ndk_api = 23

android.archs = arm64-v8a

android.accept_sdk_license = True

android.private_storage = True

[buildozer]

log_level = 2
warn_on_root = 1
