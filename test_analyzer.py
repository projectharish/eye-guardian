from camera_analyzer import CameraAnalyzer
config = {
    'camera': {'camera_index': 0, 'optimal_distance_cm': 50, 'distance_tolerance_cm': 10},
    'posture_analysis': {'slouch_threshold': 20}
}
analyzer = CameraAnalyzer(config)
res = analyzer.get_quick_analysis()
print("Analysis Result:", res)
