from monte_carlo import monte_carlo_equity, monte_carlo_ff_sizing,monte_carlo_mdd_sizing
import pandas as pd

if __name__ == '__main__':

    wf_trade_list = pd.read_csv()

    monte_carlo_mdd_sizing(wf_trade_list, equity=10000,
                       margin_req=0.05, iterations=100,
                       contract_value=1000,max_drawdown=300)


    monte_carlo_equity(wf_trade_list, starting_equity=10000,
                       margin_req=0.05, iterations=100,
                       contract_size=50, contract_value=1000,
                       ending_equity=20000, increment=1000)

    monte_carlo_ff_sizing(wf_trade_list, equity=10000,
                       margin_req=0.05, iterations=100,
                       contract_value=1000,start_sizing=1,
                       end_sizing=5, increment = 1,
                          max_drawdown=300)
