import json
import os
import numpy as np
from argparse import ArgumentParser
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from CP.src.launch import solve_CP
# from SAT.src.launch import solve_SAT
# from SMT.src.launch import solve_SMT


def plot_board(width, height, blocks, args, i, rotation, show_plot=False, show_axis=False):
    cmap = plt.cm.get_cmap('nipy_spectral', len(blocks))
    fig, ax = plt.subplots(figsize=(10, 10))
    for component, (w, h, x, y) in enumerate(blocks):
        label = f'{w}x{h}, ({x},{y})'
        if rotation is not None:
            label += f', R={1 if rotation[component] else 0}'
        ax.add_patch(Rectangle((x, y), w, h, facecolor=cmap(component), edgecolor='k', label=label, lw=2, alpha=0.8))
    ax.set_ylim(0, height)
    ax.set_xlim(0, width)
    ax.set_xlabel('width', fontsize=15)
    ax.set_ylabel('length', fontsize=15)
    ax.legend()
    ax.set_title(f'Instance {i}, size (WxH): {width}x{height}', fontsize=22)
    if not show_axis:
        ax.set_xticks([])
        ax.set_yticks([])
    plt.savefig(f'{args.technology}/out/fig-ins-{i}.png')
    if show_plot:
        plt.show(block=False)
        plt.pause(1)
    plt.close(fig)


def get_timings(args):
    if not os.path.exists('timings'):
        os.mkdir('timings')
    name = f'timings/{args.technology}{"-a" if args.area else ""}' \
           f'{"-sb" if args.sb else ""}' \
           f'{"-rot" if args.rotation else ""}'
    if args.technology == 'CP':
        name += f'-heu{args.heu}-restart{args.restart}'
    elif args.technology == 'src':
        name += f'{"-search" if args.sat_search else ""}'
    elif args.technology == 'SMT':
        name += f'-{args.smt_model}'
    name += '.json'
    if os.path.isfile(name):  # z3 I hate your timeout bug so much
        with open(name) as f:
            data = {int(k): v for k, v in json.load(f).items()}
    else:
        data = {}
    return data, name


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('technology', type=str, help='The technology to use (CP, src or SMT)')
    parser.add_argument('-s', '--start', type=int, help='First instance to solve', default=1)
    parser.add_argument('-e', '--end', type=int, help='Last instance to solve', default=39)
    parser.add_argument('-t', '--timeout', type=int, help='Timeout (ms)', default=300000)
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    parser.add_argument('-a', '--no-area', dest="area", action="store_false", help="do not order circuits by area", default=True)
    parser.add_argument('-r', '--rotation', action="store_true", help="enables circuits rotation")
    parser.add_argument('-sb', '--symmetry-breaking', dest="sb", action="store_true", help="enables symmetry breaking", default=False)

    # technology-specific arguments
    parser.add_argument('--solver', type=str, help='CP solver (default: chuffed)', default='chuffed')
    parser.add_argument('--heu', type=str, help='CP search heuristic (default: input_order, min)', default='input_order')
    parser.add_argument('--restart', type=str, help='CP restart strategy (default: luby)', default='luby')

    parser.add_argument('--sat-search', action="store_true", help="enables custom z3 sat search")

    parser.add_argument('--smt-model', type=str, help='SMT model to use (default: base)', default='base')

    args = parser.parse_args()
    args.technology = args.technology.upper()
    params = {'rotation': args.rotation}
    if args.technology == 'CP':
        solver = solve_CP
        if args.solver not in ('gecode', 'chuffed'):
            raise ValueError(f'wrong solver {args.solver}; supported ones are gecode and chuffed')
        if args.heu not in ('input_order', 'first_fail', 'dom_w_deg'):
            raise ValueError(f'wrong search heuristic {args.heu}; supported ones are (input_order, first_fail, dom_w_deg)')
        if args.restart not in ('none', 'luby', 'geom'):
            raise ValueError(f'wrong restart {args.restart}; supported ones are (none, luby, geom)')
        params.update({'solver': args.solver, 'search_heuristic': args.heu, 'restart_strategy': args.restart,
                       'sb': args.sb})
    elif args.technology == 'src':
        solver = solve_SAT
        params.update({'custom_search': args.sat_search})
    elif args.technology == 'SMT':
        solver = solve_SMT
        if args.smt_model not in ('base', 'array'):
            raise ValueError(f'wrong smt model {args.smt_model}; supported ones are "base", "array"')
        params.update({'sb': args.sb, 'kind': args.smt_model})
    else:
        raise ValueError('Wrong technology, either CP, src or SMT')

    if not os.path.exists(f'{args.technology}/out'):
        os.mkdir(f'{args.technology}/out')
    print('*' * 42)
    print(f'SOLVING INSTANCES {args.start} - {args.end} USING {args.technology} MODEL')
    print(f'PARAMETERS: {params}')
    print('*' * 42)
    timings, timings_filename = get_timings(args)

    # Solves the instances in the specified interval
    for i in range(args.start, args.end + 1):
        print('=' * 20)
        print(f'INSTANCE {i}')
        with open(f'instances/ins-{i}.txt') as f:
            lines = f.readlines()
        if args.verbose:
            print(''.join(lines))
        lines = [l.strip('\n') for l in lines]
        w = int(lines[0].strip('\n'))
        n = int(lines[1].strip('\n'))
        dim = [l.split(' ') for l in lines[2:]]
        x, y = list(zip(*map(lambda xy: (int(xy[0]), int(xy[1])), dim)))
        xy = np.array([x, y]).T

        # Sorts circuits by area
        if args.area:
            areas = np.prod(xy, axis=1)
            sorted_idx = np.argsort(areas)[::-1]
            xy = xy[sorted_idx]
            x = list(map(int, xy[:, 0]))
            y = list(map(int, xy[:, 1]))

        min_area = np.prod(xy, axis=1).sum()
        minh = int(min_area / w)
        xy[:, 0] = xy[:, 0].max()
        oversized_area = np.prod(xy, axis=1).sum()
        maxh = int(oversized_area / w)

        # initialize instance dictionary
        instance = {"w": w, 'n': n, 'inputx': x, 'inputy': y, 'minh': minh, 'maxh': maxh, 'rotation': None}
        instance = solver(instance, **params)

        if instance['solved']:
            # creates output string
            out = f"{instance['w']} {instance['h']}\n{instance['n']}\n"
            out += '\n'.join([f"{xi} {yi} {xhati} {yhati}"
                              for xi, yi, xhati, yhati in zip(instance['x'], instance['y'],
                                                              instance['xhat'], instance['yhat'])])
            if args.verbose:
                print(out)
            print(f'TIME: {instance["fulltime"]}')
            timings[i] = instance['time']

            # writes output file
            with open(f'{args.technology}/out/out-{i}.txt', 'w') as f:
                f.write(out)

            # save result
            res = [(xi, yi, xhati, yhati)
                   for xi, yi, xhati, yhati in zip(instance['x'], instance['y'], instance['xhat'], instance['yhat'])]
            plot_board(instance['w'], instance['h'], res, args, i, instance['rotation'])
        else:
            timings[i] = 300.

        # write runtime to json file
        with open(timings_filename, 'w') as f:
            json.dump(timings, f)
