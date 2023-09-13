## The TERRA grid

The TERRA grid is based on a regular icosahedron projected onto a sphere. 
This defines twenty equal spherical triangles from the original 12 points. 
To generate a mesh of required resolution the midpoints of the three sides of each spherical triangle are connected using a great circle. 
This divides it into four sub triangles. 
This process can be repeated successively to get to the desired lateral resolution. 
Radially, TERRA nests these meshes vertically above each other to divide up the whole volume of the shell. 
The number of nested meshes is (m/2+1), where m is the number of sub-divisions along the side of an original triangle. 
These nested meshes are usually distributed uniformly radially from the inner to the outer shell. 
This is described in more detail in @Baumgardner1985. 

This means that at the kth refinement, there are 2 + 10m2 nodes, and 20m2 triangles, where m = 2k in each layer mesh. 
There would be m/2 + 1 such layers nested radially. 
For example at the 6th refinement, k=6, m=64 – there are 81,920 triangles, and 40,962 nodes in each layer, and 33 layers – giving 1,351,746 nodes in total. 

The unknowns solved for in the mantle convection equations, i.e. dynamic pressure, mantle velocity and temperature, are solved on the nodes. 
Therefore, there are five unknowns at each node. 

![Terra Grid](https://github.com/mantle-convection-constrained/terratools/tree/main/docs/grid.png "This figure shows the original icosahedron, and three refinements from a to d.")
