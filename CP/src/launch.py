from minizinc import Instance, Model, Solver
from minizinc.result import Status
from datetime import timedelta


def solve_CP(instance, sb, rotation, solver, search_heuristic, restart_strategy, timeout=300000):
    mod = ''
    if sb:
        mod += '-sb'
    if rotation:
        mod += '-rot'
    model = Model(f"CP/src/vlsi{mod}.mzn")
    gecode = Solver.lookup(solver)
    mzn = Instance(gecode, model)

    # initializes model variables
    mzn["w"] = instance['w']
    mzn['n'] = instance['n']
    if rotation:
        mzn['inputx'] = instance['inputx']
        mzn['inputy'] = instance['inputy']
    else:
        mzn['x'] = instance['inputx']
        mzn['y'] = instance['inputy']
    mzn['minh'] = instance['minh']
    mzn['maxh'] = instance['maxh']
    mzn['search'] = search_heuristic
    mzn['restart'] = restart_strategy

    processes = -1 if solver == 'gecode' else None
    result = mzn.solve(timeout=timedelta(milliseconds=timeout), processes=processes)
    if result.status == Status.OPTIMAL_SOLUTION:
        output = {'solved': True, 'h': result.objective, 'xhat': result['xhat'], 'yhat': result['yhat'],
                  'x': result['x'] if rotation else instance['inputx'],
                  'y': result['y'] if rotation else instance['inputy'],
                  'fulltime': f'total: {result.statistics["time"]}',
                  'time': (result.statistics['time'].microseconds / (10 ** 6)) + result.statistics['time'].seconds,
                  'rotation': result['rotation'] if rotation else None}
    else:
        output = {'solved': False}
    instance.update(output)
    if instance['solved']:
        print('SOLVED')
    else:
        print('NOT SOLVED WITHIN TIME LIMIT')
    return instance
