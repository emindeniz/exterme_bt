import backtrader as bt
import pandas as pd
def print_analysis(strategy,filename,writer=None,stop=True):
    """
    Function to print results of a single strategy from a run
    :param strategy:
    :param filename:
    :param writer:
    :param stop:
    :return:
    """

    # Get the names of analyzers that are added to the run.
    names = strategy.analyzers.getnames()

    if writer is None:
        writer = bt.WriterFile(out=filename, csv=True)

    # First print parameters of the strategy:
    writer.writedict(strategy.params.__dict__)
    # Print each analysis one by one the file
    for name in names:
        analysis = strategy.analyzers.getbyname(name)
        # from IPython import embed
        # embed()
        writer.writedict(analysis.get_analysis())

    # Stop the writer
    if stop:
        writer.stop()

def print_optimization(opt_res,filename):
    """
    Print results of an optimization run.
    :param opt_res:
    :param filename:
    :return:
    """

    # Get the element 0 (there was only 1 strategy in each run) of each optimization
    # In future there could be multiple
    st0 = [s[0] for s in opt_res]

    writer = bt.WriterFile(out=filename, csv=True)

    # For each run print the analysis to the file.
    for run in st0:
        print_analysis(run, filename, writer=writer, stop=False)
    writer.stop()

def flatten_dict(odict,first_prefix=''):
    def helper(current_dict,prefix):
        for key,value in current_dict.items():
            if isinstance(value,dict):
                helper(value,prefix=prefix+'_'+key)
            else:
                result[prefix+'_'+key]=value

    result = {}
    helper(odict,first_prefix)
    return result

def flatten_analysis(strategy):

    # Get the names of analyzers that are added to the run.
    names = strategy.analyzers.getnames()

    analysis_dict = {}
    # First print parameters of the strategy:
    analysis_dict.update({'value':strategy.thevalue})
    analysis_dict.update(strategy.params.__dict__)
    # Flatten each analysis dict
    for name in names:
        analysis = strategy.analyzers.getbyname(name)
        analysis_dict.update(
            flatten_dict(
                analysis.get_analysis(),first_prefix=name))

    return analysis_dict



def flatten_optimization(opt_res):
    """
    Print results of an optimization run.
    :param opt_res:
    :param filename:
    :return:
    """

    # Get the element 0 (there was only 1 strategy in each run) of each optimization
    # In future there could be multiple
    st0 = [s[0] for s in opt_res]

    optimization_res = pd.DataFrame()
    # For each run print the analysis to the file.
    for run in st0:
        current_strategy = flatten_analysis(run)
        optimization_res = optimization_res.append(
            pd.DataFrame(current_strategy,index=[0]),
            ignore_index=True)

    return optimization_res







