import sys

import numpy as np
from configparser import ConfigParser

sys.path.insert(0, 'src/')

import test_artery as ta
from artery_network import Artery_Network
from utils import *
from utils import is_near as near


def get_parameters(config_location):
	"""Read parameters for tests from file.
	:param config_location: Location of config file
	:return: The parameters needed for testing
	"""
	config = ConfigParser()
	config.read(config_location)

	# Constructor parameters
	order = config.getint('Parameters', 'order')
	rc = config.getfloat('Parameters', 'rc')
	qc = config.getfloat('Parameters', 'qc')
	Ru = np.array([float(f) for f in config.get('Parameters', 'Ru').split(',')])
	Rd = np.array([float(f) for f in config.get('Parameters', 'Rd').split(',')])
	L = np.array([float(f) for f in config.get('Parameters', 'L').split(',')])
	k1 = config.getfloat('Parameters', 'k1')
	k2 = config.getfloat('Parameters', 'k2')
	k3 = config.getfloat('Parameters', 'k3')
	rho = config.getfloat('Parameters', 'rho')
	nu = config.getfloat('Parameters', 'nu')
	p0 = config.getfloat('Parameters', 'p0')
	R1 = config.getfloat('Parameters', 'R1')
	R2 = config.getfloat('Parameters', 'R2')
	CT = config.getfloat('Parameters', 'CT')
	

	# Geometry parameters
	Nt = config.getint('Geometry', 'Nt')
	Nx = config.getint('Geometry', 'Nx')
	T = config.getfloat('Geometry', 'T')
	N_cycles = config.getint('Geometry', 'N_cycles')

	# Solution parameters
	output_location = config.get('Solution', 'output_location')
	theta = config.getfloat('Solution', 'theta')
	Nt_store = config.getint('Solution', 'Nt_store')
	N_cycles_store = config.getint('Solution', 'N_cycles_store')
	store_area = config.getint('Solution', 'store_area')
	store_pressure = config.getint('Solution', 'store_pressure')
	q0 = config.getfloat('Solution', 'q0')
	q_half = config.getfloat('Solution', 'q_half')
	
	# Adimensionalise parameters
	Ru, Rd, L, k1, k2, k3, Re, nu, p0, R1, R2, CT, q0, T =\
		adimensionalise_parameters(rc, qc, Ru, Rd, L, k1, k2, k3,
								   rho, nu, p0, R1, R2, CT, q0, T)
	q_half = adimensionalise(rc, qc, rho, q_half, 'flow')
	
	return order, rc, qc, Ru, Rd, L, k1, k2, k3, rho, Re, nu, p0, R1, R2, CT, Nt, Nx, T, N_cycles, output_location, theta, Nt_store, N_cycles_store, store_area, store_pressure, q0, q_half




def test_constructor(order, rc, qc, Ru, Rd, L, k1, k2, k3, rho, Re, nu, p0, R1, R2, CT):
	"""Construct artery network.
	Test correct assignment of parameters.
	Test correct structure of network.
	:param order: Number of arterial levels
	:param rc: Characteristic radius (length)
	:param qc: Characteristic flow
	:param Ru: Upstream radii
	:param Rd: Downstream radii
	:param L: Vessel lengths
	:param k1: First constant from the relation Eh/r0
	:param k2: Second constant from the relation Eh/r0
	:param k3: Third constant from the relation Eh/R0
	:param rho: Density of blood
	:param Re: Reynolds' number
	:param nu: Viscosity of blood
	:param p0: Diastolic pressure
	:param R1: First resistance from Windkessel model
	:param R2: Second resistance from Windkessel model
	:param CT: Compliance from Windkessel model
	:return: Constructed artery network
	"""
	an = Artery_Network(order, rc, qc, Ru, Rd, L, k1, k2, k3, rho, Re, nu, p0, R1, R2, CT)
	
	assert(an.order == order)
	assert(len(an.arteries) == 2**order-1)
	assert(an.range_arteries == range(2**order-1))
	assert(an.range_parent_arteries == range(2**(order-1)-1))
	assert(an.range_daughter_arteries == range(1, 2**order-1))
	assert(an.range_end_arteries == range(2**(order-1)-1, 2**order-1))
	assert(an.rc == rc)
	assert(an.qc == qc)
	assert(an.rho == rho)
	assert(an.R1 == R1)
	assert(an.R2 == R2)
	assert(an.CT == CT)
	
	for i, artery in enumerate(an.arteries):
		assert(artery.root_vessel if i==0 else not artery.root_vessel)
		assert(artery.end_vessel if i in an.range_end_arteries\
			   else not artery.end_vessel)
	
	return(an)


def test_define_geometry(an, Nx, Nt, T, N_cycles):
	"""Define geometry on artery network.
	Test correct assignment of parameters.
	"""
	an.define_geometry(Nx, Nt, T, N_cycles)

	assert(an.Nx == Nx)
	assert(an.Nt == Nt)
	assert(near(an.T, T))
	assert(an.N_cycles == N_cycles)


def test_define_solution(an, output_location, q0, theta):
	"""Define solution on artery network.
	Test correct assignment of parameters.
	"""
	an.define_solution(output_location, q0, theta)
	
	assert(an.output_location == output_location)
	assert(an.theta == theta)


def test_daughter_arteries(an):
	"""Test correct finding of daughter vessels.
	"""
	for ip in an.range_parent_arteries:
		i1, i2 = an.daughter_arteries(ip)
		assert(i1 == 2*ip+1)
		assert(i2 == 2*ip+2)


def test_parent_artery(an):
	"""Test correct indices for parent vessels.
	"""
	for i in an.range_daughter_arteries:
		ip = an.parent_artery(i)
		if i % 2 == 1:
			assert(ip == (i-1)//2)
		else:
			assert(ip == (i-2)//2)


def test_sister_artery(an):
	"""Test correct indices for sister vessel.
	"""
	for i in an.range_daughter_arteries:
		s = an.sister_artery(i)
		if i % 2 == 1:
			assert(s == i+1)
		else:
			assert(s == i-1)


def test_flux(an):
	"""Test correct behaviour of flux function.
	"""
	for a in an.arteries:
		for x in np.linspace(0, a.L, 100):
			U = a.Un(x)
			anflux = an.flux(a, U, x)
			F1 = U[1]
			F2 = U[1]**2 + a.f(x)*np.sqrt(a.A0(x)*U[0])
			assert(near(anflux[0], F1))
			assert(near(anflux[1], F2))


def test_source(an):
	"""Test correct behaviour of source function.
	"""
	for a in an.arteries:
		for x in np.linspace(0, a.L, 100):
			U = a.Un(x)
			ansource = an.source(a, U, x)
			S2 = - 2*np.sqrt(np.pi)/a.db/a.Re*U[1]/np.sqrt(U[0]) + (2*np.sqrt(U[0])*(np.sqrt(np.pi)*a.f(x) + np.sqrt(a.A0(x))*a.dfdr(x)) - U[0]*a.dfdr(x))*a.drdx(x)
			assert(near(ansource[0], 0))
			assert(near(ansource[1], S2))


def test_compute_U_half(an):
	"""Test correct behaviour of compute_U_half.
	"""
	for a in an.arteries:
		for x in [[0, a.dex], [a.L-a.dex, a.L]]:
			U0, U1 = a.Un(x[0]), a.Un(x[1])
			an_U_half = an.compute_U_half(a, U0, U1, x[0], x[1])
			F0, S0 = an.flux(a, U0, x[0]), an.source(a, U0, x[0])
			F1, S1 = an.flux(a, U1, x[1]), an.source(a, U1, x[1])
			U_half = (U0+U1)/2 - a.dt/a.dex*(F1-F0) + a.dt/4*(S0+S1)
			assert(near(an_U_half[0], U_half[0]))
			assert(near(an_U_half[1], U_half[1]))


def test_compute_A_out(an):
	"""Test correct behaviour of compute_A_out.
	"""
	for a in an.arteries:
		A_out = an.compute_A_out(a)


def test_initial_x(an):
	"""Test correct assignment of parameters.
	"""
	for ip in an.range_parent_arteries:
		i1, i2 = an.daughter_arteries(ip)
		p, d1, d2 = an.arteries[ip], an.arteries[i1], an.arteries[i2]
		x = an.initial_x(p, d1, d2)
		for xi in x[:3]: assert(near(xi, p.q0))
		for xi in x[3:6]: assert(near(xi, d1.q0))
		for xi in x[6:9]: assert(near(xi, d2.q0))
		for xi in x[9:12]: assert(near(xi, p.A0(p.L)))
		for xi in x[12:15]: assert(near(xi, d1.A0(0)))
		for xi in x[15:]: assert(near(xi, d2.A0(0)))


def test_define_x(an):
	"""Test correct value for x.
	"""
	an.define_x()
	for ip in an.range_parent_arteries:
		i1, i2 = an.daughter_arteries(ip)
		p, d1, d2 = an.arteries[ip], an.arteries[i1], an.arteries[i2]
		x = an.initial_x(p, d1, d2)
		for i in range(18):
			assert(near(an.x[ip, i], x[i]))


def test_problem_function(an):
	"""Test correct behaviour of problem_function.
	For the right (analytical) value of x, the function should take zero-values.
	By perturbing a given x, certain components should be zero.
	"""
	x = np.ones(18)
	for ip in an.range_parent_arteries:
		i1, i2 = an.daughter_arteries(ip)
		p, d1, d2 = an.arteries[ip], an.arteries[i1], an.arteries[i2]
		
		Um1p, Um0p = p.Un(p.L-p.dex), p.Un(p.L)
		U0d1, U1d1 = d1.Un(0), d1.Un(d1.dex)
		U0d2, U1d2 = d2.Un(0), d2.Un(d2.dex)

		U_half_p = an.compute_U_half(p, Um1p, Um0p, p.L-p.dex, p.L)
		U_half_d1 = an.compute_U_half(d1, U0d1, U1d1, 0, d1.dex)
		U_half_d2 = an.compute_U_half(d2, U0d2, U1d2, 0, d2.dex)
		
		F_half_p = an.flux(p, U_half_p, p.L-p.dex/2)
		F_half_d1 = an.flux(d1, U_half_d1, d1.dex/2)
		F_half_d2 = an.flux(d2, U_half_d2, d2.dex/2)
		S_half_p = an.source(p, U_half_p, p.L-p.dex/2)
		S_half_d1 = an.source(d1, U_half_d1, d1.dex/2)
		S_half_d2 = an.source(d2, U_half_d2, d2.dex/2)
		
		# Abbreviation
		def F(x):
			return an.problem_function(p, d1, d2, x)
		
		# 0
		x[1] = (U_half_p[1] + x[2])/2
		assert(near(F(x)[0], 0))
		x[1] = 1

		# 1
		x[4] = (x[5] + U_half_d1[1])/2
		assert(near(F(x)[1], 0))
		x[4] = 1

		# 2 
		x[7] = (x[8] + U_half_d2[1])/2
		assert(near(F(x)[2], 0))
		x[7] = 1

		# 3
		x[10] = (U_half_p[0] + x[11])/2
		assert(near(F(x)[3], 0))
		x[10] = 1

		# 4
		x[13] = (x[14] + U_half_d1[0])/2
		assert(near(F(x)[4], 0))
		x[13] = 1

		# 5 
		x[16] = (x[17] + U_half_d2[0])/2
		assert(near(F(x)[5], 0))
		x[16] = 1


def test_jacobian(an):
	"""Test that the analytical expression for the jacobian matrix is close to a numerically computed jacobian.
	"""
	# Higher tolerance since the numerical jacobian is inaccurate
	tol = 1.e-3
	reltol = 1.e-3
	
	# h gets absorbed in x if it is too small
	h = 1.e-8
	
	for ip in an.range_parent_arteries:
		i1, i2 = an.daughter_arteries(ip)
		p, d1, d2 = an.arteries[ip], an.arteries[i1], an.arteries[i2]
		x = np.ones(18)
		he = np.zeros(18)
		J = an.jacobian(p, d1, d2, x)
		F = an.problem_function(p, d1, d2, x)
		for j in range(18):
			he[j] = h
			Fph = an.problem_function(p, d1, d2, x+he)
			dF = (Fph-F)/h
			for i in range(18):
				assert(near(J[i, j], dF[i], tol, reltol))
			he[j] = 0


def test_newton(an):
	"""Test correct results from newton function.
	"""
	for ip in an.range_parent_arteries:
		i1, i2 = an.daughter_arteries(ip)
		p, d1, d2 = an.arteries[ip], an.arteries[i1], an.arteries[i2]
		x = an.initial_x(p, d1, d2)
		x = an.newton(p, d1, d2, x, 1000, 1.e-14)
		FF = an.problem_function(p, d1, d2, x)
		
		# After solving, all components of FF should be zero
		for F in FF: assert(near(F, 0, 1.e-11))
		
		# x represents areas and flows, that should be strictly positive
		for xi in x: assert(xi > 1.e-12)


def test_adjust_bifurcation_step(an):
	"""Test correct behaviour of adjust_bifurcation_step function.
	"""
	for ip in an.range_parent_arteries:
		i1, i2 = an.daughter_arteries(ip)
		p, d1, d2 = an.arteries[ip], an.arteries[i1], an.arteries[i2]
		for margin in [0.1, 0.05, 1.e-4, 1.e-8]:
			an.adjust_bifurcation_step(p, d1, d2, margin)
			assert(p.check_CFL(p.L, p.Un(p.L)[0], p.Un(p.L)[1]))
			assert(d1.check_CFL(0, d1.Un(0)[0], d1.Un(0)[1]))
			assert(d2.check_CFL(0, d2.Un(0)[0], d2.Un(0)[1]))


def test_set_inner_bc(an):
	"""Test correct assignment of inner boundary conditions.
	Test that the CFL condition is verified.
	"""
	for ip in an.range_parent_arteries:
		i1, i2 = an.daughter_arteries(ip)
		p, d1, d2 = an.arteries[ip], an.arteries[i1], an.arteries[i2]
		
		an.define_x()
		an.set_inner_bc(ip, i1, i2)
		
		# Test that the CFL-condition is verified
		assert(p.check_CFL(p.L, p.Un(p.L)[0], p.Un(p.L)[1]))
		assert(d1.check_CFL(0, d1.Un(0)[0], d1.Un(0)[1]))
		assert(d2.check_CFL(0, d2.Un(0)[0], d2.Un(0)[1]))

		x = an.initial_x(p, d1, d2)
		x = an.newton(p, d1, d2, x, 1000, 1.e-14)
		
		assert(near(p.U_out[0], x[9]))
		assert(near(p.U_out[1], x[0]))
		assert(near(d1.U_in[0], x[12]))
		assert(near(d1.U_in[1], x[3]))
		assert(near(d2.U_in[0], x[15]))
		assert(near(d2.U_in[1], x[6]))


def test_set_bcs(an):
	"""Test correct assignment of boundary conditions.
	"""
	q_in = an.arteries[0].q0
	an.set_bcs(q_in)
	
	assert(near(an.arteries[0].q_in, q_in)) 


def test_dump_metadata(an, Nt_store, N_cycles_store, store_area, store_pressure):
	"""Test correct execution of dump_metadata.
	"""
	an.dump_metadata(Nt_store, N_cycles_store, store_area, store_pressure)
	
	order, Nx, Nt, T0, T, L, rc, qc, rho, mesh_locations, names, locations = \
		read_output(an.output_location+'/data.cfg')
	
	assert(order == an.order)
	assert(Nx == an.Nx)
	assert(Nt == Nt_store*N_cycles_store)
	assert(near(T0, an.T*(an.N_cycles-N_cycles_store)))
	assert(near(T, an.T*an.N_cycles))
	for i in range(len(L)): assert(near(L[i], an.arteries[i].L))
	assert(near(rc, an.rc))
	assert(near(qc, an.qc))
	assert(near(rho, an.rho))
	for i in range(len(mesh_locations)):
		assert(mesh_locations[i] ==\
			   ('%s/mesh_%i.xml.gz' % (an.output_location, i)))

	i = 0
	assert(names[i] == 'flow')
	if store_area:
		i += 1
		assert(names[i] == 'area')
	if store_pressure:
		i += 1
		assert(names[i] == 'pressure')

	for i in range(len(locations)):
		assert(locations[i] == ('%s/%s' % (an.output_location, names[i])))


def test_solve(an, q0, q_half, Nt_store, N_cycles_store, store_area,
			   store_pressure):
	"""
	"""
	q_first = np.linspace(q0, q_half, an.Nt//2)
	q_second = np.linspace(q_half, q0, an.Nt//2)
	print(len(q_first), type(q_first))
	print(len(q_second), type(q_second))

	q_ins = np.concatenate([q_first, q_second])
	an.solve(q_ins, Nt_store, N_cycles_store, store_area, store_pressure)


def test_artery_network(config_location):
	"""Test correct functionality of the methods from the artery_network class.
	"""
	order, rc, qc, Ru, Rd, L, k1, k2, k3, rho, Re, nu, p0, R1, R2, CT, Nt, Nx,\
		T, N_cycles, output_location, theta, Nt_store, N_cycles_store,\
		store_area, store_pressure, q0, q_half = get_parameters(config_location)
	
	an = test_constructor(order, rc, qc, Ru, Rd, L, k1, k2, k3, rho, Re, nu,\
						  p0, R1, R2, CT)

	test_daughter_arteries(an)

	test_parent_artery(an)

	test_sister_artery(an)

	test_define_geometry(an, Nx, Nt, T, N_cycles)

	test_define_solution(an, output_location, q0, theta)

	test_flux(an)

	test_source(an)

	test_compute_U_half(an)

	test_compute_A_out(an)

	test_initial_x(an)

	test_define_x(an)

	test_problem_function(an)

	test_jacobian(an)

	test_newton(an)

	test_adjust_bifurcation_step(an)

	test_set_inner_bc(an)

	test_set_bcs(an)

	test_dump_metadata(an, Nt_store, N_cycles_store, store_area, store_pressure)

	test_solve(an, q0, q_half, Nt_store, N_cycles_store, store_area,
			   store_pressure)


if __name__ == '__main__':
	test_artery_network(sys.argv[1])
