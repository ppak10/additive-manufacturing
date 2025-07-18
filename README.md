# additive-manufacturing
Additive Manufacturing related software modules

## Getting Started
1. Installation
```bash
pip install additive-manufacturing
```

2. Create a new `Workspace`:
```bash
am workspace init test
```

3. Navigate to workspace directory and initialize segmenter
```bash
am segmenter init
```

4. Convert `.gcode` file to segments
```bash
am segmenter parse overhang.gcode --units mm
```

5. Create solver.
```
python manage.py solver_init model=eagar-tsai device=cuda:0
```

7. Create simulation.
```
python manage.py simulation_init 
```

8. Run simulation.
```
python manage.py simulation_run_layer_index layer_index=99
```

9. Visualize simulation
```
python manage.py simulation_visualize_layer_segments num_proc=16
```

## Solver

## Segmenter
- Visualize GCode
```
python manage.py segmenter_visualize_layer_index layer_index=1
```

```
python manage.py segmenter_visualize_all_layers num_proc=16
```


## References

```bibtex
@article{
	title = {Thermal control of laser powder bed fusion using deep reinforcement learning},
	volume = {46},
	issn = {2214-8604},
	url = {https://www.sciencedirect.com/science/article/pii/S2214860421001986},
	doi = {10.1016/j.addma.2021.102033},
	journal = {Additive Manufacturing},
	author = {Ogoke, Francis and Farimani, Amir Barati},
	month = oct,
	year = {2021},
	keywords = {Additive Manufacturing, Deep Reinforcement Learning, Powder Bed Fusion},
	pages = {102033},
}
```

```bibtex
@phdthesis{
	address = {United States -- California},
	type = {Ph.{D}.},
	title = {Physics-{Based} {Surrogate} {Modeling} of {Laser} {Powder} {Bed} {Fusion} {Additive} {Manufacturing}},
	copyright = {Database copyright ProQuest LLC; ProQuest does not claim copyright in the individual underlying works.},
	url = {https://www.proquest.com/docview/2503475225/abstract/71F47FA688874C02PQ/1},
	language = {English},
	school = {University of California, Davis},
	author = {Wolfer, Alexander James},
	year = {2020},
	note = {ISBN: 9798582546023},
	keywords = {Additive Manufacturing, Bayesian statistics, Mechanical engineering, Powder bed fusion, Surrogate model, Uncertainty quantification},
}
```

```bibtex
@article{
	title = {Fast solution strategy for transient heat conduction for arbitrary scan paths in additive manufacturing},
	volume = {30},
	issn = {2214-8604},
	url = {https://www.sciencedirect.com/science/article/pii/S2214860419303446},
	doi = {10.1016/j.addma.2019.100898},
	journal = {Additive Manufacturing},
	author = {Wolfer, Alexander J. and Aires, Jeremy and Wheeler, Kevin and Delplanque, Jean-Pierre and Rubenchik, Alexander and Anderson, Andy and Khairallah, Saad},
	month = dec,
	year = {2019},
	keywords = {Additive manufacturing, Gaussian convolution, Heat conduction, Powder bed fusion, Semi-analytical model},
	pages = {100898},
}
```

```bibtex
@article{
	title = {The {Theory} of {Moving} {Sources} of {Heat} and {Its} {Application} to {Metal} {Treatments}},
	volume = {68},
	issn = {0097-6822},
	url = {https://doi.org/10.1115/1.4018624},
	doi = {10.1115/1.4018624},
	number = {8},
	journal = {Transactions of the American Society of Mechanical Engineers},
	author = {Rosenthal, D.},
	month = dec,
	year = {2022},
	pages = {849--865},
}
```
