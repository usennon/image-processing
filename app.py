from flask import Flask, render_template, request, flash
import os
import numpy as np
import pandas as pd
from matplotlib.colors import rgb2hex
from scipy.cluster.vq import whiten, kmeans
from PIL import Image
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv(key='TOKEN')

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


@app.route('/', methods=['GET', 'POST'])
def main():
    filename = None
    colors = []
    if request.method == 'POST':
        colors = extract()
        filenames = os.listdir(os.path.join(APP_ROOT, 'static/images/'))
        if len(filenames) < 2:
            filename = filenames[0]
        else:
            filename = filenames[1]
    return render_template('index.html',
                           imgname=filename,
                           colors=colors)


def extract():
    target = upload()
    directory = os.listdir(target)
    if len(directory) < 2:
        image = np.asarray(Image.open(target + (directory[0])))
    else:
        image = np.asarray(Image.open(target + (directory[1])))

    r = []
    g = []
    b = []
    for row in image:
        for temp_r, temp_g, temp_b in row:
            r.append(temp_r)
            g.append(temp_g)
            b.append(temp_b)

    batman_df = pd.DataFrame({'red': r,
                              'green': g,
                              'blue': b})

    # Scaling the values
    batman_df['scaled_color_red'] = whiten(batman_df['red'])
    batman_df['scaled_color_blue'] = whiten(batman_df['blue'])
    batman_df['scaled_color_green'] = whiten(batman_df['green'])

    clusters_count = int(request.form.get('num'))

    cluster_centers, _ = kmeans(batman_df[['scaled_color_red',
                                           'scaled_color_blue',
                                           'scaled_color_green']],
                                clusters_count)

    dominant_colors = []

    red_std, green_std, blue_std = batman_df[['red',
                                              'green',
                                              'blue']].std()
    for cluster_center in cluster_centers:
        red_scaled, green_scaled, blue_scaled = cluster_center
        dominant_colors.append((
            red_scaled * red_std / 255,
            green_scaled * green_std / 255,
            blue_scaled * blue_std / 255
        ))
    hex_colors = [rgb2hex(dominant_colors[i]) for i in range(len(dominant_colors))]
    return hex_colors


def upload():
    file = request.files.get('file')

    target = os.path.join(APP_ROOT, 'static/images/')

    filelist = [f for f in os.listdir(target)]
    for f in filelist:
        if filelist.index(f) > 0:
            os.remove(os.path.join(target, f))

    if not os.path.isdir(target):
        os.mkdir(target)

    filename = file.filename

    destination = "".join([target, filename])
    try:
        file.save(destination)
    except PermissionError:
        pass

    return target


if __name__ == '__main__':
    app.run(debug=True)
