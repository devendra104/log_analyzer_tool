"""  QE Test Result Analyzer """
from multiprocessing import Process

from views import pagination_support


def run_rest_api():
    pagination_support.app.run(host="0.0.0.0", port=5001, debug=False)


if __name__ == "__main__":
    rest_api_process = Process(target=run_rest_api)
    rest_api_process.start()
