from walk_forward import run_walk_forward,run_walk_forward_multi
from configs.SMACrossoverMultiConfig import getConfig

if __name__ == '__main__':

    walkforward_input = getConfig()

    run_walk_forward_multi(**walkforward_input)


