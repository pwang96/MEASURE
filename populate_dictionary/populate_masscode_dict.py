__author__ = 'masslab'


def populate_massInfo(main, massInfo, workdown):
    """

    :param main: main_dict, populated
    :param massInfo: empty massInfo dictionary, initialized in masscode_dicts.py
    :return: populated massInfo dictionary ready to be put into masscode
    """
    massInfo['nominal'] = [float(i[0][16:26].strip()) for i in main['weight info']]

    if not workdown:
        massInfo['acceptcorrect'] = [float(i[0][46:58].strip()) for i in main['weight info']]

    massInfo['cgravity'] = main['cg differences']
    massInfo['volume'] = []
    massInfo['density'] = [float(i[0][26:36].strip()) for i in main['weight info']]
    massInfo['coexpans'] = [float(i[0][36:46].strip()) for i in main['weight info']]
    massInfo['config'] = main['design matrix']
    massInfo['restraintpos'] = main['restraint vec']
    massInfo['checkpos'] = main['check vec']
    massInfo['restraintnew'] = main['next restraint vec']

    for pos, element in enumerate(main['addon info']):
        position_vector = [0]*len(main['addon info'])  # make a vector for the positions e.g. [0,0,1,0]
        if element:
            position_vector[pos] = 1

            for addon in main['addon info'][pos]:
                massInfo['add'].append([position_vector,
                                        float(addon[0][26:38].strip()),  # addon weight in g
                                        0,  # volume
                                        float(addon[0][44:54].strip()),  # density
                                        float(addon[0][16:26].strip())])  # coefficient of expansion

    massInfo['balstd'] = [0.01, float(main['balance std dev'])]  # TODO: find between uncert, set to 0.01 now

    if not workdown:
        massInfo['error'] = [0, float(main['restraint uncert'])]

    massInfo['envirouncertainty'] =[float(main['temperature uncert']), float(main['humidity uncert']),
                                    float(main['pressure uncert']), 0.00005]  # CO2: 0.00005
    massInfo['volumecov'] = []
    massInfo['sensitivity'] = []
    massInfo['envirocorrection'] = {'temp': [], 'press': [], 'humid': []}  # TODO: get the correction coefficients

    return massInfo