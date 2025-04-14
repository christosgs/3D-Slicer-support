# Define the names of segments you want to keep
segments_to_keep = [
    "GTV", "CTV", "DUODENUM", "PANCREAS", "LARGEBOWEL",
    "SMALLBOWEL", "GREATVESSEL", "STOMACH", "LIVER_HEALTHY",
    "OARSUM", "CENTRALHEPATRACT", "PORTALVENA", 
    "CRITICALSTRUCTUR", "ADAPTIVERING"
]

# Iterate through all segmentations in the scene
for segmentation_node in slicer.util.getNodesByClass("vtkMRMLSegmentationNode"):
    segmentation = segmentation_node.GetSegmentation()

    # Create a list of segments to be removed
    segments_to_remove = []

    # Collect segments to remove based on the names
    for segment_index in range(segmentation.GetNumberOfSegments()):
        segment_id = segmentation.GetNthSegmentID(segment_index)
        segment = segmentation.GetSegment(segment_id)
        segment_name = segment.GetName()

        # If the segment is not in the list to keep, mark it for removal
        if segment_name not in segments_to_keep:
            segments_to_remove.append(segment_id)

    # Remove the segments that are not needed
    for segment_id in segments_to_remove:
        segmentation.RemoveSegment(segment_id)

# Refresh the 3D Slicer scene
slicer.app.processEvents()

print("Unwanted segments removed, only specified segments retained.")
