import slicer
import numpy as np
import csv

def initialize_table():
     
    # Initialize a new table node with appropriate columns for metrics.
    
    table_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTableNode', 'Segmentation Metrics Table')

    # Add columns to the table node
    table_node.AddColumn().SetName('Segment Comparison')
    table_node.AddColumn().SetName('Segment Name')
    table_node.AddColumn().SetName('Dice Coefficient')
    table_node.AddColumn().SetName('True Positives (%)')
    table_node.AddColumn().SetName('True Negatives (%)')
    table_node.AddColumn().SetName('False Positives (%)')
    table_node.AddColumn().SetName('False Negatives (%)')
    table_node.AddColumn().SetName('Maximum Hausdorff Distance (mm)')
    table_node.AddColumn().SetName('Average Hausdorff Distance (mm)')
    table_node.AddColumn().SetName('95% Hausdorff Distance (mm)')
    table_node.AddColumn().SetName('Reference Center')
    table_node.AddColumn().SetName('Compare Center')
    table_node.AddColumn().SetName('Reference Volume (cc)')
    table_node.AddColumn().SetName('Compare Volume (cc)')

    return table_node

def append_metrics_to_table(table_node, metrics, reference_name, compare_name, segment_name):
    
    # Append a row of metrics to the specified table node.
    
    if not table_node:
        raise ValueError("Table node is not initialized.")

    # Combine the reference and compare names
    comparison_label = f"{reference_name}-{compare_name}"

    # Create a new row and populate it with metrics
    row = table_node.AddEmptyRow()
    table_node.SetCellText(row, 0, comparison_label)  # Combined label
    table_node.SetCellText(row, 1, segment_name)
    table_node.SetCellText(row, 2, f"{metrics.get('dice_coefficient', 'N/A'):.4f}")
    table_node.SetCellText(row, 3, f"{metrics.get('true_positives', 'N/A'):.2f}")
    table_node.SetCellText(row, 4, f"{metrics.get('true_negatives', 'N/A'):.2f}")
    table_node.SetCellText(row, 5, f"{metrics.get('false_positives', 'N/A'):.2f}")
    table_node.SetCellText(row, 6, f"{metrics.get('false_negatives', 'N/A'):.2f}")
    table_node.SetCellText(row, 7, f"{metrics.get('maximum_hausdorff', 'N/A'):.2f}")
    table_node.SetCellText(row, 8, f"{metrics.get('average_hausdorff', 'N/A'):.2f}")
    table_node.SetCellText(row, 9, f"{metrics.get('hausdorff_95', 'N/A'):.2f}")
    table_node.SetCellText(row, 10, str(metrics.get('reference_center', 'N/A')))
    table_node.SetCellText(row, 11, str(metrics.get('compare_center', 'N/A')))
    table_node.SetCellText(row, 12, f"{metrics.get('reference_volume', 'N/A'):.2f}")
    table_node.SetCellText(row, 13, f"{metrics.get('compare_volume', 'N/A'):.2f}")

def compute_metrics(reference_segmentation_node, comparison_segmentation_node, segment_name):
    """
    Compute detailed metrics for comparing two segments using Segment Comparison logic.
    """
    # Get segment IDs
    reference_segment_id = reference_segmentation_node.GetSegmentation().GetSegmentIdBySegmentName(segment_name)
    compare_segment_id = comparison_segmentation_node.GetSegmentation().GetSegmentIdBySegmentName(segment_name)

    if not reference_segment_id or not compare_segment_id:
        return None

    # Create a new SegmentComparison node
    param_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentComparisonNode")
    param_node.SetAndObserveReferenceSegmentationNode(reference_segmentation_node)
    param_node.SetReferenceSegmentID(reference_segment_id)
    param_node.SetAndObserveCompareSegmentationNode(comparison_segmentation_node)
    param_node.SetCompareSegmentID(compare_segment_id)

    # Perform the comparison
    segment_comparison_logic = slicer.modules.segmentcomparison.logic()
    segment_comparison_logic.ComputeDiceStatistics(param_node)
    segment_comparison_logic.ComputeHausdorffDistances(param_node)

    # Retrieve results from the parameter node
    dice_coefficient = param_node.GetDiceCoefficient()
    true_positives = param_node.GetTruePositivesPercent()
    true_negatives = param_node.GetTrueNegativesPercent()
    false_positives = param_node.GetFalsePositivesPercent()
    false_negatives = param_node.GetFalseNegativesPercent()

    maximum_hausdorff = param_node.GetMaximumHausdorffDistanceForBoundaryMm()
    average_hausdorff = param_node.GetAverageHausdorffDistanceForBoundaryMm()
    hausdorff_95 = param_node.GetPercent95HausdorffDistanceForVolumeMm()

    # Retrieve volumes and centers of mass
    def get_segment_labelmap(segmentation_node, segment_id):
        # Create a new LabelMapVolumeNode
        labelmap_volume_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
        # Use the segmentation logic to convert the segment to labelmap
        slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentation_node, labelmap_volume_node)
        return labelmap_volume_node

    def compute_volume(labelmap_node):
        image_data = labelmap_node.GetImageData()
        voxel_count = np.prod(image_data.GetDimensions())
        spacing = labelmap_node.GetSpacing()
        volume = voxel_count * np.prod(spacing) / 1000.0  # Convert to cubic centimeters
        return volume

    def compute_center_of_mass(labelmap_node):
        image_data = labelmap_node.GetImageData()
        array = slicer.util.arrayFromVolume(labelmap_node)
        coords = np.indices(array.shape)
        center_of_mass = np.sum(coords * array, axis=(1, 2, 3)) / np.sum(array)
        spacing = np.array(labelmap_node.GetSpacing())
        origin = np.array(labelmap_node.GetOrigin())
        center_of_mass = np.multiply(center_of_mass, spacing) + origin
        return center_of_mass

    reference_segment_labelmap_node = get_segment_labelmap(reference_segmentation_node, reference_segment_id)
    compare_segment_labelmap_node = get_segment_labelmap(comparison_segmentation_node, compare_segment_id)

    reference_volume = compute_volume(reference_segment_labelmap_node)
    compare_volume = compute_volume(compare_segment_labelmap_node)

    reference_center = compute_center_of_mass(reference_segment_labelmap_node)
    compare_center = compute_center_of_mass(compare_segment_labelmap_node)

    # Clean up the comparison node and labelmap nodes
    slicer.mrmlScene.RemoveNode(param_node)
    slicer.mrmlScene.RemoveNode(reference_segment_labelmap_node)
    slicer.mrmlScene.RemoveNode(compare_segment_labelmap_node)

    return {
        "dice_coefficient": dice_coefficient,
        "true_positives": true_positives,
        "true_negatives": true_negatives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "maximum_hausdorff": maximum_hausdorff,
        "average_hausdorff": average_hausdorff,
        "hausdorff_95": hausdorff_95,
        "reference_center": reference_center,
        "compare_center": compare_center,
        "reference_volume": reference_volume,
        "compare_volume": compare_volume
    }

def export_table_to_csv(table_node, file_path):
    % """
    % Export the MRML table node to a CSV file.
    % """
    if not table_node:
        raise ValueError("Table node is not initialized.")

    # Get table columns and rows
    columns = [table_node.GetColumnName(c) for c in range(table_node.GetNumberOfColumns())]
    rows = table_node.GetNumberOfRows()

    # Open the file for writing
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(columns)  # Write column headers
        
        # Write rows
        for r in range(rows):
            row_data = [table_node.GetCellText(r, c) for c in range(len(columns))]
            writer.writerow(row_data)

    print(f"Table exported to {file_path}")

# Define the names of segments to compare
segments_to_compare = ["GTV", "CTV", "DUODENUM", "SMALLBOWEL", "LARGEBOWEL", "GREATVESSEL", "STOMACH"]

# Load segmentation nodes
reference_segmentation_node = slicer.util.getNode("RTSTRUCT: SBRTANDET24_1")
fraction_segmentation_nodes = [slicer.util.getNode(f"RTSTRUCT: ADAPTDAY{i}_1") for i in range(1, 4)]

# Initialize the table
table_node = initialize_table()

# Iterate through each fraction and compare segments
for fraction_index, fraction_segmentation_node in enumerate(fraction_segmentation_nodes, start=1):
    for segment_name in segments_to_compare:
        metrics = compute_metrics(reference_segmentation_node, fraction_segmentation_node, segment_name)
        if metrics is not None:
            append_metrics_to_table(table_node, metrics, reference_segmentation_node.GetName(), fraction_segmentation_node.GetName(), segment_name)

# Export the table to CSV
csv_file_path = slicer.app.temporaryPath + "/segmentation_metrics_table"+ datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
export_table_to_csv(table_node, csv_file_path)

print("All metrics appended to table.")
