#!/usr/bin/env python
import PySimpleGUI as sg
import Functions as f
import matplotlib.pyplot as plt
from mpl_point_clicker import clicker
import cv2
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import numpy as np
import csv


# Table field names
fields = ['SSID', 'BSSID', 'RSSI', 'CHANNEL', 'HT', 'CC', 'SECURITY']

# Image file types
file_types = [("JPEG (*.jpg)", "*.jpg"),
              ("All files (*.*)", "*.*")]

# ------ Make the Table Data ------
data = []
headings = fields


legend = " "

# Create the window and set its size to the screen resolution
screen_resolution = sg.Window.get_screen_size()

# ------ Window Layout c------
tab1_layout = [[sg.Table(values=data, headings=headings, max_col_width=50,
                         auto_size_columns=False,
                         def_col_width=20,
                         display_row_numbers=False,
                         justification='left',
                         num_rows=35,
                         key='-TABLE-',
                         font='Courier 18',
                         selected_row_colors='black on lightgray',
                         enable_events=True,
                         text_color='white',
                         expand_x=True,
                         expand_y=False,
                         vertical_scroll_only=False,
                         select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                         # Comment out to not enable header and other clicks
                         enable_click_events=True,
                         )],
               [sg.Button('Scan'),
                sg.Button('Delete'), sg.Button('CSV'), sg.Button('Exit')]
               ]

Second_layout = [
    [sg.Input(
        size=(1, 1), key="-FILE-", visible=False), sg.FileBrowse(file_types=file_types), sg.B('Import'), sg.B('HeatMap'), sg.Canvas(key='controls_cv',)],
    [sg.T('Figure:', visible=False)],
    [sg.Column(
        layout=[
            [sg.Canvas(key='fig_cv',
                       # it's important that you set this size
                       size=(600 * 2, 900)
                       )]
        ],
        pad=(0, 0)
    )],
]


Third_layout = [

    [sg.Button('Validate')],
    [sg.Column(
        layout=[
            [sg.Canvas(key='fig_cv_1',
                       # it's important that you set this size
                       size=(600 * 2, 900)
                       )]
        ],
        pad=(0, 0)
    )
    ]
]


tab2_layout = [
    [sg.Column(Second_layout, expand_x=True, element_justification='center')
     ]
]

tab3_layout = [
    [sg.Column(Third_layout, expand_x=True, element_justification='center')
     ]
]


# main layout
layout = [[sg.TabGroup([[sg.Tab('Discover', tab1_layout, key='-mykey-'),
                        sg.Tab('Survey', tab2_layout),
                        sg.Tab('Validation', tab3_layout)]], key='-group1-', tab_location='top', selected_title_color='white')]]


window = sg.Window('Indoor Wifi Survey Tool', layout,
                   size=screen_resolution, resizable=False, finalize=True)


while True:
    event, values = window.read()

    fig = None
    ax = None

    if event == sg.WIN_CLOSED or event == 'Exit':
        break

    elif event == 'Scan':
        new_data = f.get_data()
        window['-TABLE-'].update(values=new_data)

    elif event == 'CSV':
        f.make_csv(new_data)

    elif event == 'Delete':
        if values['-TABLE-'] == []:
            sg.popup('No Row selected')
        else:
            del new_data[values['-TABLE-'][0]]
            window['-TABLE-'].update(values=new_data)

    elif event == 'Import':
        pic = plt.imread(values["-FILE-"])
        pic = cv2.cvtColor(pic, cv2.COLOR_BGR2RGB)
        import_size = pic.shape[:2]
        fig = plt.figure(frameon=False)
        ax = fig.add_subplot()
        ax.imshow(pic)
        ax.tick_params(labelsize="xx-small")
        ax.axis('off')
        klicker = clicker(ax, [legend], markers=['o'], colors="red")
        DPI = fig.get_dpi()
        fig.set_size_inches(500 * 2 / float(DPI), 800 / float(DPI))
        klicker.on_class_changed(f.class_changed_cb)
        klicker.on_point_added(f.point_added_cb)
        klicker.on_point_removed(f.point_removed_cb)

        f.draw_figure_w_toolbar(
            window['fig_cv'].TKCanvas, fig, window['controls_cv'].TKCanvas)

    elif event == 'HeatMap':
        xcoordinates, ycoordinates, rssi = f.average(
            'Data/floor5.csv')
        xco = xcoordinates
        yco = ycoordinates
        rv = rssi
        # Call plot_porosity_estimate and get the heat map data, pass 'import_size' instead of 'image_size'
        zstar = f.plot_porosity_estimate(xco, yco, rv, import_size)

        # Write the estimate values to a new CSV file
        with open('Data/estimate_values.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in zstar:
                writer.writerow(row)

        red = mcolors.colorConverter.to_rgb('#FF0000')
        green = mcolors.colorConverter.to_rgb('#00FF00')
        cmap = mcolors.LinearSegmentedColormap.from_list(
            'mycmap', [red, green], N=10)

        # Overlay the heat map on top of the imported image, set the extent of the overlay image to match the extent of the imported image
        fig = plt.figure()
        ax = fig.add_subplot()
        ax.imshow(pic)

        # Add the scatter plot of the x and y coordinates here
        cax = plt.scatter(xco, yco, s=5, c='black')
        # vmin, vmax = -80, -100
        heatmap = ax.imshow(zstar, alpha=0.8, cmap=cmap, interpolation='sinc',
                            extent=[0, import_size[1], import_size[0], 0])

        ax.axis('off')  # remove axis border
        DPI = fig.get_dpi()
        fig.set_size_inches(500 * 2 / float(DPI), 800 / float(DPI))

        cbar = plt.colorbar(heatmap, orientation='vertical',
                            shrink=0.5, pad=0.05, aspect=10)
        cbar.ax.tick_params(labelsize="xx-small")
        cbar.ax.set_ylabel('RSSI', rotation=270, labelpad=15, fontsize='small')

        f.draw_figure_w_toolbar(
            window['fig_cv'].TKCanvas, fig, window['controls_cv'].TKCanvas)

    elif event == 'Validate':
        xcoordinates, ycoordinates, rssi = f.Validation_points(
            'Data/18_floor5.csv')
        gt_x = xcoordinates
        gt_y = ycoordinates
        gt_phi = rssi

        # Call plot_porosity_estimate and get the heat map data, pass 'import_size' instead of 'image_size'
        zstar = f.Validation(gt_x, gt_y, gt_phi, xcoordinates, ycoordinates)

        # Calculate the root mean square error (RMSE) and mean absolute error (MAE)
        rmse = np.sqrt(np.mean((zstar - gt_phi)**2))
        mae = np.mean(np.abs(zstar - gt_phi))
        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

        red = mcolors.colorConverter.to_rgb('#FF0000')
        green = mcolors.colorConverter.to_rgb('#00FF00')
        cmap = mcolors.LinearSegmentedColormap.from_list(
            'mycmap', [red, green], N=10)

        # Plot the original data in the first subplot
        ax1.scatter(gt_x, gt_y, c=gt_phi, cmap=cmap, s=50)
        ax1.set_title('Ground Truth', fontsize=11)
        ax1.invert_yaxis()  # invert the y-axis

        # Plot the estimated data in the second subplot
        ax2.scatter(xcoordinates, ycoordinates, c=zstar, cmap=cmap, s=50)
        ax2.set_title('Estimated', fontsize=11)
        ax2.invert_yaxis()  # invert the y-axis

        # Remove numerical labels on the x and y axis
        ax1.set_xticklabels([])
        ax1.set_yticklabels([])
        ax2.set_xticklabels([])
        ax2.set_yticklabels([])

        # Add a colorbar to the second subplot
        cbar = fig.colorbar(ax2.collections[0], ax=ax2)
        cbar.set_label('RSSI')

        # Show the root mean square error (RMSE) and mean absolute error (MAE) in the plot title
        fig.suptitle(f'RMSE: {rmse:.13f}, MAE: {mae:.13f}', fontsize=12)

        f.draw_figure_w_toolbar(
            window['fig_cv_1'].TKCanvas, fig, window['controls_cv'].TKCanvas)


window.close()
