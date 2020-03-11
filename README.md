# Custom Simulator

Custom Simulator is a collection of scripts developed to read memory traces generated by HEVC and VVC Test Models(HM and VTM, respectively), extract the information and plot graphs displaying the results.

## Results

### Inter-prediction specific memory analysis

The inter-frame prediction is the most resource-intensive operation in both HEVC and VVC. Considering this, a specific analysis was performed as a way to measure the increased VVC memory requirements in comparison with HEVC. The HM and VTM software applications were extended to generate memory trace files detailing the accesses to the candidate blocks and their required volume of fetched data.

#### Inter-prediction overall memory accesses

![Inter prediction overall graph](/samples/graphs/Inter_prediction_overall_mem_analysis.png)

#### Inter-prediction memory accesses per CU size

![HM Block memory graph](/samples/graphs/HM_block_mem_graph.png)
![VTM Block memory graph](/samples/graphs/VTM_block_mem_graph.png)

### Overall memory profiling

The overall memory profiling was performed using the Intel® VTune™ Amplifier profiling tool to monitor the volume of memory loads (read accesses) and stores (write accesses) of each module.

#### Memory accesses profiling per encoding module

![VTM Block memory graph](/samples/graphs/memory_breakdown.png)

## Parameters

The parameters used for the analysis can be found in `custom_simulator.py`.

The default values are:

```python
# Parameters
FRAMES = '17'
SEARCH_RANGE = ['96']
```

## Instructions

The instructions on how to run the scripts are available [in this repository](https://github.com/arthurcerveira/Video-Memory-Analysis-Environment).
