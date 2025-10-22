from pygrabber.dshow_graph import FilterGraph

# Create a FilterGraph object to find devices
graph = FilterGraph()

# Get the list of available video input devices
# This is what OpenCV's default DSHOW backend should see
devices = graph.get_input_devices()

if not devices:
    print("Error: No video capture devices found!")
    print("This confirms the driver is not correctly registered with Windows.")
else:
    print("Available video devices:")
    for i, device_name in enumerate(devices):
        print(f"  Index {i}: {device_name}")