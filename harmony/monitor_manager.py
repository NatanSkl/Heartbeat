from monitors import ConvertToPdfMonitor


monitors = [ConvertToPdfMonitor()]

for monitor in monitors:
    monitor.check_pulses()
    print(monitor.pulse_errors)
