
from bokeh.io import show
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, RangeTool
from bokeh.plotting import figure, output_file
from bokeh.io import output_notebook
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from matplotlib.dates import num2date
import seaborn as sns


def plot_observer(strategy,alias='value',notebook=False):
    """
    Plot an observer line with alias. If alias is value
    this is the equity line.
    :param strategy:
    :param alias:
    :param notebook:
    :return:
    """
    for observer in strategy.getobservers():
        linealias = observer.lines._getlinealias(0)
        if linealias ==alias:
            dates = np.array(strategy.datetime.plot())
            ydata = np.array(observer.lines[0].plot())
            dates = num2date(dates)
            plot_bokeh_dates_vs_values(dates=dates,
                                       values=ydata,
                                       notebook=notebook,
                                       alias=alias)

    return

def plot_bokeh_dates_vs_values(dates, values, notebook=False,
                               alias='value'):
    """
    Useful function to create an interactive plot of dates vs values
    :param dates:
    :param values:
    :param notebook:
    :return:
    """
    TOOLS = "pan,wheel_zoom,box_zoom,reset,save"

    source = ColumnDataSource(data=dict(date=dates, value=values))

    p = figure(plot_height=300, plot_width=600, tools=TOOLS,
               x_axis_type="datetime", x_axis_location="above",
               background_fill_color="#efefef", x_range=(dates[0], dates[-1]))

    p.line('date', 'value', source=source)
    p.yaxis.axis_label = 'value'

    select = figure(title="Drag the middle and edges of the selection box to change the range above",
                    plot_height=130, plot_width=600, y_range=p.y_range,
                    x_axis_type="datetime", y_axis_type=None,
                    tools="", toolbar_location=None, background_fill_color="#efefef")

    range_rool = RangeTool(x_range=p.x_range)
    range_rool.overlay.fill_color = "navy"
    range_rool.overlay.fill_alpha = 0.2

    select.line('date', 'value', source=source)
    select.ygrid.grid_line_color = None
    select.add_tools(range_rool)
    select.toolbar.active_multi = range_rool

    if notebook:
        output_notebook()
    else:
        output_file("{}.html".format(alias),
                    title="{} observer".format(alias))

    show(column(p, select))


def countour_plot(df, X=None,Y=None,Z=None):
    X = df[X].values
    Y= df[Y].values
    Z= df[Z].values

    num_x = np.unique(X).shape[0]
    num_y = np.unique(Y).shape[0]

    X = X.reshape(num_x,num_y,order='F')
    Y = Y.reshape(num_x,num_y,order='F')
    Z = Z.reshape(num_x,num_y,order='F')

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_surface(X, Y, Z, rstride=8, cstride=8, alpha=0.3)
    cset = ax.contour(X, Y, Z, zdir='z', offset=-100, cmap=cm.coolwarm)
    cset = ax.contour(X, Y, Z, zdir='x', offset=-40, cmap=cm.coolwarm)
    cset = ax.contour(X, Y, Z, zdir='y', offset=40, cmap=cm.coolwarm)

    plt.show()

    # Plot the surface.
    surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm,
                           linewidth=0, antialiased=False)

    # Customize the z axis.
    ax.set_zlim(-1.01, 1.01)
    ax.zaxis.set_major_locator(LinearLocator(10))
    ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

    # Add a color bar which maps values to colors.
    fig.colorbar(surf, shrink=0.5, aspect=5)

    plt.show()


    ### Plot #2
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    # Plot the surface.
    surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm,
                           linewidth=0, antialiased=False)

    # Customize the z axis.
    ax.zaxis.set_major_locator(LinearLocator(10))
    ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

    # Add a color bar which maps values to colors.
    fig.colorbar(surf, shrink=0.5, aspect=5)

    plt.show()

def heatmap(df, X=None,Y=None,Z=None):

    df = df.pivot(X, Y, Z)
    ax = sns.heatmap(df,cmap=sns.dark_palette("seagreen",reverse=True))

    plt.show()

