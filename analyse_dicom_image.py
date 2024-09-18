import pydicom as dicom
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from cellpose import models, io
from skimage.measure import regionprops
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array, array_to_img
from matplotlib.patches import Circle
import os


def analyse_dicom_image(image_path, flow_threshold=0.4, cellprob_threshold=0.0, model_path='trained_resnet50_model.h5'):
    # Step 1: Loading the DICOM image
    dicom_data = dicom.dcmread(image_path)
    image = dicom_data.pixel_array

    # Save the initial image as a PNG
    initial_image_name = 'initial_image.png'
    initial_image_path = os.path.join('uploads', initial_image_name)
    plt.imsave(initial_image_path, image, cmap='gray')

    # Step 2: Initialising the Cellpose model and segmenting cells
    model = models.Cellpose(gpu=False, model_type='cyto2')

    # Setting parameters for evaluation
    channels = [0, 0] 

    # Segmenting the image with custom options
    masks, flows, styles, diams = model.eval(
        image, 
        diameter=0, 
        channels=channels,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold
    )

    print(f"Automatically calculated average cell diameter: {diams}")

    # Define the minimum allowed diameter
    min_allowed_diameter = 0.5 * diams
    print(f"Minimum allowed diameter for filtering: {min_allowed_diameter}")

    # Save the segmented masks
    io.imsave('masks.png', masks)

    # Step 3: Loading the pre-trained ResNet50 model
    resnet_model = load_model(model_path)

    # Preprocessing cell image for ResNet50
    def preprocess_cell_image(cell_image):
        cell_image = array_to_img(cell_image)
        cell_image = cell_image.resize((224, 224))
        cell_image = img_to_array(cell_image)
        cell_image = np.expand_dims(cell_image, axis=0)
        cell_image = cell_image / 255.0  # Normalise to [0, 1] range
        return cell_image

    # Step 4: Extracting individual cells
    props = regionprops(masks)
    num_cells = 0
    infected_count = 0

    # Step 5: Preparing to draw circles around infected cells
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(image, cmap='gray')

    for prop in props:
        cell_diameter = prop.equivalent_diameter
        if cell_diameter >= min_allowed_diameter:  
            num_cells += 1
            minr, minc, maxr, maxc = prop.bbox
            cell_image = image[minr:maxr, minc:maxc]
            preprocessed_cell_image = preprocess_cell_image(cell_image)

            # Predict using ResNet50 model
            prediction = resnet_model.predict(preprocessed_cell_image)
            label = 'infected' if prediction[0][0] > 0.5 else 'uninfected'

            if label == 'infected':
                infected_count += 1
                # Calculate the center and radius for the circle
                center_y = (minr + maxr) / 2
                center_x = (minc + maxc) / 2
                radius = max(maxr - minr, maxc - minc) / 2
                # Draw the circle
                circle = Circle((center_x, center_y), radius, color='red', fill=False, linewidth=2)
                ax.add_patch(circle)

    # Step 6: Printing total cell count and infected cell count
    total_cell_count = num_cells
    infected_cell_count = infected_count
    patient_status = "Infected" if infected_cell_count > 0 else "Not Infected"

    # Saving the overlay image
    ax.axis('off')
    processed_image_name = 'processed_image_with_circles.png'
    processed_image_path = os.path.join('uploads', processed_image_name)
    plt.savefig(processed_image_path)
    plt.close()

    return total_cell_count, infected_cell_count, patient_status, initial_image_path, processed_image_path
