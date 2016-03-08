# -*- coding: utf-8 -*-
"""
Evolutionary solution to the camera position.\

Created on Thu Jun  4 10:06:30 2015

@author: yosef
"""
import signal

import numpy as np, matplotlib.pyplot as pl
import numpy.random as rnd
from matplotlib import cm

from optv.calibration import Calibration
from calib import pixel_2D_coords, simple_highpass, detect_ref_points

wrap_it_up = False
def interrupt(signum, frame):
    global wrap_it_up
    wrap_it_up = True
    
signal.signal(signal.SIGINT, interrupt)

def get_pos(inters, R, angs):
    # Transpose of http://planning.cs.uiuc.edu/node102.html
    # Also consider the angles are reversed when moving from camera frame to
    # global frame.
    s = np.sin(angs)
    c = np.cos(angs)
    pos = inters + R*np.r_[ s[1], -c[1]*s[0], c[1]*c[0] ]
    return pos
    
def gen_calib(inters, R, angs, glass_vec, prim_point, radial_dist, decent):
    pos = get_pos(inters, R, angs)
    cal = Calibration()
    cal.set_pos(pos)
    cal.set_angles(angs)
    cal.set_primary_point(prim_point)
    cal.set_radial_distortion(radial_dist)
    cal.set_decentering(decent)
    cal.set_affine_trans(np.r_[1,0])
    cal.set_glass_vec(glass_vec)

    return cal
    
def fitness(solution, calib_targs, calib_detect, glass_vec, cpar):
    """
    Checks the fitness of an evolutionary solution of calibration values to 
    target points. Fitness is the sum of squares of the distance from each 
    guessed point to the closest neighbor.
    
    Arguments:
    solution - array, concatenated: position of intersection with Z=0 plane; 3 
        angles of exterior calibration; primary point (xh,yh,cc); 3 radial
        distortion parameters; 2 decentering parameters.
    calib_targs - a (p,3) array of p known points on the calibration target.
    calib_detect - a (d,2) array of d detected points in the calibration 
        target.
    cpar - a ControlParams object with image data.
    """
    # Calculate exterior position:
    inters = np.zeros(3)
    inters[:2] = solution[:2]
    R = solution[2]
    angs = solution[3:6] 
    prim_point = solution[6:9]
    rad_dist = solution[9:12]
    decent = solution[12:14]
        
    # Set calibration object 
    cal = gen_calib(inters, R, angs, glass_vec, prim_point, rad_dist, decent)
    
    #print pixel_2D_coords(cal, calib_targs, cpar)
    known_2d = pixel_2D_coords(cal, calib_targs, cpar)
    #print known_2d
    
    dists = np.linalg.norm(
        known_2d[None,:,:] - calib_detect[:,None,:], axis=2).min(axis=0)
    
    return np.sum(dists**2)

def mutation(solution, bounds):
    gene = rnd.random_integers(0, len(solution) - 1)
    minb, maxb = bounds[gene]
    solution[gene] = rnd.rand()*(maxb - minb) + minb

def recombination(sol1, sol2):
    genes = rnd.random_integers(0, 1, len(sol1))
    ret = sol1.copy()
    ret[genes == 1] = sol2[genes == 1]
    return ret

# Main part
import sys, yaml
from mixintel.openptv import control_params

yaml_file = sys.argv[1]
yaml_args = yaml.load(file(yaml_file))
control_args = yaml_args['scene']
cpar = control_params(**control_args)
cam = yaml_args['target']['number']

fname = yaml_args['target']['image']
calblock_name = yaml_args['target']['known_points']
glass_vec = np.r_[yaml_args['target']['glass_vec']]

image = pl.imread(fname)
hp = simple_highpass(image, cpar)

tarr = detect_ref_points(hp, cam, cpar)
targs = np.array([t.pos() for t in tarr])

pop_size = 1500
#bounds = [(100., 200.), (-120, 0), (-150, -400), (-1, 0), (-1, 0), (-0.1, 0.1)]
#bounds = [(100., 200.), (-120, 0), (150, 400), (np.pi - 1, np.pi + 1), (-1, 0), (-0.1, 0.1)]
##bounds = [(100., 200.), (-120, 0), (-150, -400), (-np.pi, np.pi), (-np.pi, np.pi), (-np.pi, np.pi)]
if cam == 0:
    bounds = [(-20.,20.), (-20.,20.), # offset
              (210.,300.), # R
              (-0.3, 0.3), (np.pi-0.3, np.pi+0.3), (-0.5, 0.5), # angles
              (-0.05, 0.05), (-0.05, 0.05), (70, 90), # primary point
              (-1e-5, 1e-5), (-1e-5, 1e-5), (-1e-5, 1e-5), # radial distortion
              (-1e-5, 1e-5), (-1e-5, 1e-5) # decentering
    ]
    cal_points = np.loadtxt(calblock_name)[:,1:]
elif cam == 1:
    #bounds = [(-100., 100.), (-120, 0), (-200, -400), (-1, 1), (np.pi/2, 1.5*np.pi), (-1, 1)]
    bounds = [(-20.,20.), (-20.,20.), (210.,300.), (-0.3, 0.3), (np.pi-0.3, np.pi+0.3), (-0.5, 0.5)]
    cal_points = np.loadtxt(calblock_name)[:,1:]
elif cam == 2:
    #bounds = [(-150., 150.), (-120, 0), (250, 500), (-1, 1), (-1, 1), (-1, 1)]
    bounds = [(-20.,20.), (-20.,20.), (210.,300.), (-0.4, 0.4), (-0.3, 0.3), (-0.3, 0.3)]
    cal_points = np.loadtxt(calblock_name)[:,1:]
elif cam == 3:
    #bounds = [(50., 250.), (-120, 0), (200, 400), (-1, 1), (-1, 1), (-1, 1)]
    bounds = [(-20.,20.), (-20.,20.), (210.,300.), (-0.3, 0.3), (-0.3, 0.3), (-0.3, 0.3)]
    cal_points = np.loadtxt(calblock_name)[:,1:]
    
init_sols = np.array([
    np.r_[[rnd.rand()*(maxb - minb) + minb for minb, maxb in bounds]
    ] for s in xrange(pop_size)])

fits = []
for sol in init_sols:
    fits.append( fitness(sol, cal_points, targs, glass_vec, cpar) )
fits = np.array(fits)
print fits

def show_current(signum, frame):
    best_fit = np.argmin(fits)
    inters = np.zeros(3)
    inters[:2] = init_sols[best_fit][:2]
    R = init_sols[best_fit][2]
    angs = init_sols[best_fit][3:6]
    pos = get_pos(inters, R, angs)
    prim = init_sols[best_fit][6:9]
    rad = init_sols[best_fit][9:12]
    decent = init_sols[best_fit][12:14]

    print
    print fits[best_fit]
    print "pos/ang:"
    print "%.8f %.8f %.8f" % tuple(pos)
    print "%.8f %.8f %.8f" % tuple(angs)
    print
    print "internal: %.8f %.8f %.8f" % tuple(prim)
    print "radial distortion: %.8f %.8f %.8f" % tuple(rad)
    print "decentering: %.8f %.8f" % tuple(decent)
    
    cal = gen_calib(inters, R, angs, glass_vec, prim, rad, decent)
    init_xs, init_ys = pixel_2D_coords(cal, cal_points, cpar).T
    
    hp = simple_highpass(image, cpar)
    pl.imshow(hp, cmap=cm.gray)
    
    pl.scatter(targs[:,0], targs[:,1])
    pl.scatter(init_xs, init_ys, c='r')
    pl.scatter(init_xs[[0,-1]], init_ys[[0,-1]], c='y')

    pl.show()

signal.signal(signal.SIGTSTP, show_current)

mutation_chance = 0.7
niche_size = 50
niche_penalty = 2.
num_iters = 1000000
for it in xrange(num_iters):
    if it % 100 == 0:
        niche_size *= 0.997
        niche_penalty = niche_penalty**0.9995
    if it % 500 == 0:
        print fits.min(), fits.max()
        print niche_size, niche_penalty
    
    # Check if Ctrl-C event happened during previous iteration:
    if wrap_it_up:
        break

    # Choose breeders, chance to be chosen weighted by inverse fitness
    ranking = np.argsort(fits)
    fit_range = np.add.reduce(fits) - fits.min()
    fits_normed = (fits - fits.min())/fit_range
    
    ranked_fit = np.add.accumulate(fits_normed.max()*1.05 - fits_normed[ranking])
    if not ranked_fit.any():
        print ranked_fit
        break

    breeding_dice = rnd.rand(2) * ranked_fit[-1]
    breeders = ranking[np.digitize(breeding_dice, ranked_fit)]
    
    # choose losers
    loser = fits.argmax()
    
    # breed into losers
    newsol = recombination(*init_sols[breeders])
    mutation_dice = rnd.rand()
    if mutation_dice < mutation_chance:
        mutation(newsol, bounds)
    
    newfit = fitness(newsol, cal_points, targs, glass_vec, cpar)
    
    # Niching to avoid early convergence:
    dist = np.linalg.norm(newsol - init_sols, axis=1).min()
    if dist < niche_size:
        newfit *= niche_penalty
        #print "niching", newfit
    
    if newfit > fits[loser]:
        continue
    
    init_sols[loser] = newsol
    fits[loser] = newfit

show_current(0, 0)
