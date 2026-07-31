import os

settings_path = 'myhopestory/settings.py'
with open(settings_path, 'r', encoding='utf-8') as f:
    content = f.read()

apps = [
    "'community',",
    "'funding',",
    "'mentorship',",
    "'investors',",
    "'notifications',",
    "'analytics',",
    "'search',",
    "'resources',",
    "'events',",
    "'moderation',",
    "'dashboard',"
]

new_apps_str = "\n    ".join(apps)

content = content.replace("'core',", "'core',\n    " + new_apps_str)

with open(settings_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Settings updated.")
