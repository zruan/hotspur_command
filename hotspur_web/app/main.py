from flask import Flask, send_file
from flask import render_template
import glob
from collections import defaultdict
app = Flask(__name__)


@app.route("/")
def main():
    datasets = glob.glob("/scratch/*/*/data.json")
    dataset_dict = defaultdict(lambda : defaultdict(int))
    for dataset in datasets:
        (user,dataset_name) = dataset[9:-10].split('/')
        dataset_dict[user][dataset_name] = 1
    print(dataset_dict)
    return render_template('index.html', dataset_dict=dataset_dict)

@app.route("/<user>/<dataset>/statistics.html")
def statistics(user, dataset):
    return render_template('statistics.html')

@app.route("/<user>/<dataset>/micrograph.html")
def micrograph(user, dataset):
    return render_template('micrograph.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=8080)
