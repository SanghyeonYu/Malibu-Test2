�	���(\�@���(\�@!���(\�@      ��!       "n
=type.googleapis.com/tensorflow.profiler.PerGenericStepDetails-���(\�@�z���?1Z�b+�ju@A�HP��?I����|4d@*	33333�O@2v
?Iterator::Model::ParallelMapV2::Zip[0]::FlatMap[3]::Concatenate\ A�c̝?!LJt0�F@)��e�c]�?1�#d�m�E@:Preprocessing2F
Iterator::Model��_�L�?!��]|^g@@)� �	��?1�Tc�KJ8@:Preprocessing2U
Iterator::Model::ParallelMapV2��_vOv?!���!@)��_vOv?1���!@:Preprocessing2l
5Iterator::Model::ParallelMapV2::Zip[1]::ForeverRepeat�~j�t�x?!�*�m�"@)��ZӼ�t?1�}4�� @:Preprocessing2f
/Iterator::Model::ParallelMapV2::Zip[0]::FlatMap*��Dؠ?!�{sE�I@)ŏ1w-!o?1&%:��@:Preprocessing2Z
#Iterator::Model::ParallelMapV2::Zip䃞ͪϥ?!0)��P�P@)���_vOn?1���uX@:Preprocessing2�
NIterator::Model::ParallelMapV2::Zip[0]::FlatMap[3]::Concatenate[1]::FromTensor��H�}M?!�f�ӂ��?)��H�}M?1�f�ӂ��?:Preprocessing2x
AIterator::Model::ParallelMapV2::Zip[1]::ForeverRepeat::FromTensor��H�}M?!�f�ӂ��?)��H�}M?1�f�ӂ��?:Preprocessing2�
OIterator::Model::ParallelMapV2::Zip[0]::FlatMap[3]::Concatenate[0]::TensorSlice����Mb@?!���\�<�?)����Mb@?1���\�<�?:Preprocessing:�
]Enqueuing data: you may want to combine small input data chunks into fewer but larger chunks.
�Data preprocessing: you may increase num_parallel_calls in <a href="https://www.tensorflow.org/api_docs/python/tf/data/Dataset#map" target="_blank">Dataset map()</a> or preprocess the data OFFLINE.
�Reading data from files in advance: you may tune parameters in the following tf.data API (<a href="https://www.tensorflow.org/api_docs/python/tf/data/Dataset#prefetch" target="_blank">prefetch size</a>, <a href="https://www.tensorflow.org/api_docs/python/tf/data/Dataset#interleave" target="_blank">interleave cycle_length</a>, <a href="https://www.tensorflow.org/api_docs/python/tf/data/TFRecordDataset#class_tfrecorddataset" target="_blank">reader buffer_size</a>)
�Reading data from files on demand: you should read data IN ADVANCE using the following tf.data API (<a href="https://www.tensorflow.org/api_docs/python/tf/data/Dataset#prefetch" target="_blank">prefetch</a>, <a href="https://www.tensorflow.org/api_docs/python/tf/data/Dataset#interleave" target="_blank">interleave</a>, <a href="https://www.tensorflow.org/api_docs/python/tf/data/TFRecordDataset#class_tfrecorddataset" target="_blank">reader buffer</a>)
�Other data reading or processing: you may consider using the <a href="https://www.tensorflow.org/programmers_guide/datasets" target="_blank">tf.data API</a> (if you are not using it now)�
:type.googleapis.com/tensorflow.profiler.BottleneckAnalysis�
device�Your program is NOT input-bound because only 0.0% of the total step time sampled is waiting for input. Therefore, you should focus on reducing other time.high"�32.0 % of the total step time sampled is spent on 'Kernel Launch'. It could be due to CPU contention with tf.data. In this case, you may try to set the environment variable TF_GPU_THREAD_MODE=gpu_private.*no#You may skip the rest of this page.B�
@type.googleapis.com/tensorflow.profiler.GenericStepTimeBreakdown�
	�z���?�z���?!�z���?      ��!       "	Z�b+�ju@Z�b+�ju@!Z�b+�ju@*      ��!       2	�HP��?�HP��?!�HP��?:	����|4d@����|4d@!����|4d@B      ��!       J      ��!       R      ��!       Z      ��!       JGPUb �"8
functional_1/conv1d_6/conv1dConv2DkI�`�?!kI�`�?"j
@gradient_tape/functional_1/conv1d_42/conv1d/Conv2DBackpropFilterConv2DBackpropFilter3\�o��?!ϼ�7��?"h
?gradient_tape/functional_1/conv1d_42/conv1d/Conv2DBackpropInputConv2DBackpropInput�Z�!h�?!uAC$��?"j
@gradient_tape/functional_1/conv1d_54/conv1d/Conv2DBackpropFilterConv2DBackpropFiltern�
U�-�?!��ء��?"h
?gradient_tape/functional_1/conv1d_54/conv1d/Conv2DBackpropInputConv2DBackpropInput4o��	�?!ʭ]5�{�?"9
functional_1/conv1d_18/conv1dConv2Dy�5����?!�^�K�?"j
@gradient_tape/functional_1/conv1d_52/conv1d/Conv2DBackpropFilterConv2DBackpropFilterk��N��?!cMox�'�?"8
functional_1/conv1d_8/conv1dConv2D����:1�?!�I=&�:�?"j
@gradient_tape/functional_1/conv1d_44/conv1d/Conv2DBackpropFilterConv2DBackpropFilter9��:�?!�Y�u>�?"h
?gradient_tape/functional_1/conv1d_44/conv1d/Conv2DBackpropInputConv2DBackpropInput�/�v�d�?!tZ*�9�?Q      Y@Y��uǋ-@a�Qġ�vX@qG���W@y3͗a�Y?"�
device�Your program is NOT input-bound because only 0.0% of the total step time sampled is waiting for input. Therefore, you should focus on reducing other time.b
`input_pipeline_analyzer (especially Section 3 for the breakdown of input operations on the Host)m
ktrace_viewer (look at the activities on the timeline of each Host Thread near the bottom of the trace view)"O
Mtensorflow_stats (identify the time-consuming operations executed on the GPU)"U
Strace_viewer (look at the activities on the timeline of each GPU in the trace view)*�
�<a href="https://www.tensorflow.org/guide/data_performance_analysis" target="_blank">Analyze tf.data performance with the TF Profiler</a>*y
w<a href="https://www.tensorflow.org/guide/data_performance" target="_blank">Better performance with the tf.data API</a>2�
=type.googleapis.com/tensorflow.profiler.GenericRecommendation�
high�32.0 % of the total step time sampled is spent on 'Kernel Launch'. It could be due to CPU contention with tf.data. In this case, you may try to set the environment variable TF_GPU_THREAD_MODE=gpu_private.no*�Only 0.0% of device computation is 16 bit. So you might want to replace more 32-bit Ops by 16-bit Ops to improve performance (if the reduced accuracy is acceptable).:
Refer to the TF2 Profiler FAQb�94.2643% of Op time on the host used eager execution. Performance could be improved with <a href="https://www.tensorflow.org/guide/function" target="_blank">tf.function.</a>2"GPU(: B 