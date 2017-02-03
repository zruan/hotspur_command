from flask import Flask, send_from_directory
from flask import render_template
import glob
from collections import defaultdict
app = Flask(__name__)
debug = False


@app.route("/")
def main():
    if debug:
        datasets = glob.glob("/hotspur/scratch/*/*/data.json")
    else:
        datasets = glob.glob("/scratch/*/*/data.json")
    dataset_dict = defaultdict(lambda : defaultdict(int))
    for dataset in datasets:
        (user,dataset_name) = dataset[9:-10].split('/')[-2:]
        dataset_dict[user][dataset_name] = 1
    return render_template('index.html', dataset_dict=dataset_dict)

@app.route("/<user>/<dataset>/statistics.html")
def statistics(user, dataset):
    return render_template('statistics.html')

@app.route("/<user>/<dataset>/micrograph.html")
def micrograph(user, dataset):
    return render_template('micrograph.html')

@app.route("/<user>/<dataset>/montage.html")
def montage(user, dataset):
    return render_template('montage.html')

# Just for Debug

@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory("static/assets/",filename)

@app.route("/<user>/<dataset>/data/<path:filename>")
def data(user,dataset,filename):
    return send_from_directory("/hotspur/scratch/"+user+"/"+dataset,filename)

if __name__ == "__main__":
    debug = True
    app.run(host='0.0.0.0',debug=True, port=8282)
