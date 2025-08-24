import subprocess



path = "C:\\Users\\dario\\OneDrive\\università\\MA\\Thesis\\microscope-toolset\\microscope-toolset\\elasticsearch-7.17.29"

bin_path = f"{path}\\bin\\elasticsearch.bat"


if __name__ == '__main__':
    subprocess.Popen(
        bin_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
        shell=True
    )

#     while True:
#         process = subprocess.Popen(
#     bin_path,
#     stdout=subprocess.DEVNULL,
#     stderr=subprocess.STDOUT,
#     text=True,
#     shell=True
# )
