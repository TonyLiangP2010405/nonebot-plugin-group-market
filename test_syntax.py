import sys, os
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, "C:\\Users\\tghrt\\Documents\\nonebot-plugin-slave-market")

import nonebot
nonebot.init()
nonebot.load_plugin("nonebot_plugin_apscheduler")
nonebot.load_plugin("nonebot_plugin_localstore")

try:
    plugin = nonebot.load_plugin("nonebot_plugin_slave_market")
    if plugin:
        print("Plugin loaded successfully!")
        print(f"Matchers: {len(plugin.matcher)}")
        for m in plugin.matcher:
            print(f"  - {m}")
    else:
        print("Plugin load returned None")
except Exception as e:
    import traceback
    print(f"Plugin load failed: {e}")
    traceback.print_exc()
