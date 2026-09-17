[app]

title = School Helper
package.name = schoolhelper
package.domain = org.schoolhelper

source.dir = .
source.include_exts = py,json,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy,kivymd,plyer

orientation = portrait

fullscreen = 0

android.permissions = INTERNET,POST_NOTIFICATIONS

android.api = 35
android.minapi = 23
android.arch = arm64-v8a

[buildozer]

log_level = 2
warn_on_root = 1
