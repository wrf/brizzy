import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import seabreeze.spectrometers as sb
from scipy import signal
import progressbar
import os
import atexit
import argparse
import csv

from matplotlib import rc
rc('text', usetex=True)
plt.rcParams['text.latex.preamble'] = [
        r'\usepackage{tgheros}',    # helvetica font
        r'\usepackage{sansmath}',   # math-font matching  helvetica
        r'\sansmath'                # actually tell tex to use it!
        r'\usepackage{siunitx}',    # micro symbols
        r'\sisetup{detect-all}',    # force siunitx to use the fonts
        ]

def parse_arguments():
    """This method parses the arguments provided during command-line input
    to control how the kmers are counted. Please see the documentation for help.
    """

    #using Kevin's idea here to make te docstring the help file
    parser=argparse.ArgumentParser(description=__doc__,
                                   formatter_class=argparse.RawDescriptionHelpFormatter)

    args = parser.parse_args()
    return args

def exit_handler():
    print("You have closed the brizzy program.\nNow looking for spectra files.")
    filelist = []
    for filename in os.listdir(os.getcwd()):
        if filename.endswith(".csv"):
            filelist.append(filename)
    print("Found {} spectra, plotting".format(len(filelist)))
    bar = progressbar.ProgressBar()
    for i in bar(range(len(filelist))):
        df = pd.read_csv(filelist[i], comment = '#')
        x = df['wavelength']
        y = df['intensity']
        plot_spectrum(x, y, i, yhat=True)

def plot_spectrum(x, y, index, yhat=False):
    figWidth = 5
    figHeight = 4
    fig = plt.figure(figsize=(figWidth,figHeight))
    #set the panel dimensions
    panelWidth = 4
    panelHeight = 3
    #find the margins to center the panel in figure
    leftMargin = (figWidth - panelWidth)/2
    bottomMargin = ((figHeight - panelHeight)/2) + 0.25
    panel0 =plt.axes([leftMargin/figWidth, #left
                     bottomMargin/figHeight,    #bottom
                     panelWidth/figWidth,   #width
                     panelHeight/figHeight])     #height
    panel0.tick_params(axis='both',which='both',\
                       bottom='on', labelbottom='on',\
                       left='off', labelleft='off', \
                       right='off', labelright='off',\
                       top='off', labeltop='off')
    panel0.spines['top'].set_visible(False)
    panel0.spines['right'].set_visible(False)
    panel0.spines['left'].set_visible(False)
    panel0.set_xlim([min(x), max(x)])
    panel0.set_ylim([min(y[1:]), max(y)*1.1])
    panel0.set_xlabel("wavelength")
    panel0.plot(x,y, lw=0.50, alpha = 0.4 )
    yhat = signal.savgol_filter(y, 31, 3) # window size 51, polynomial order 3
    panel0.plot(x,yhat, color='red', alpha = 0.5)
    lambdamax = x[list(yhat).index(max(yhat))]
    panel0.axvline(x=lambdamax, color='black', lw=1.0)
    panel0.set_title("Spectrum lambda max = {}".format(int(lambdamax)))
    plt.savefig("spectrum_data_{}.png".format(index), dpi=300)

def animate(frameno, inttime, monitor):
    devices = sb.list_devices()
    spec = sb.Spectrometer(devices[0])
    spec.integration_time_micros(1000000)
    x = spec.wavelengths()
    y = spec.intensities()
    line.set_ydata(y)  # update the data
    ax.set_ylim([min(y[10:]), max(y)*1.1])
    spec.close()
    if not monitor:
        a = np.column_stack([x,y])
        np.savetxt("spectrum_data_{}.csv".format(frameno),
                   a, delimiter = ',',
                   header = "wavelength,intensity",
                   fmt = '%.14f',
                   comments="#integration time: {0} ms\n#{0}\n".format(inttime))
    return line,

def run(args):
    # Change the directory if it is specified by the user
    if args.directory:
        if not os.path.exists(args.directory):
            os.makedirs(args.directory)
        os.chdir(args.directory)
    np.set_printoptions(suppress=True)
    atexit.register(exit_handler)
    global fig
    global ax
    fig, ax = plt.subplots()
    devices = sb.list_devices()
    print("Found this device: {}".format(devices[0]))
    spec = sb.Spectrometer(devices[0])
    spec.integration_time_micros(int(args.integration_time * 1000))
    x = spec.wavelengths()
    y = spec.intensities()
    spec.close()
    global line
    line, = ax.plot(x, y, lw=1, alpha=0.5)
    ax.set_xlim([min(x), max(x)])
    ax.set_ylim([min(y[10:]), max(y)*1.1])

    ani = animation.FuncAnimation(fig, animate, blit=False,
                                  interval=args.integration_time,
                                  fargs = [args.integration_time, args.monitor],
                                  repeat=True)
    plt.show()