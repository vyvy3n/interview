---
layout: ../../layouts/Layout.astro
title: Machine Learning Interview
---

# Deep Learning

LSTM gradient vanishing problem

reduce learning rate

reduce dropout

initialization: xavier

### Dropout

train: keep prob = p, dropout = 1 - p ⇒ E = p * x + (1 - p) * 0 = px

test: w = w * p ⇒ E’ = px

implementation w/ Tensorflow

implementation demo:

```python
def dropout_forward(x, dp_param):
    p, mode = dp_param['p'], dp_param['mode']
    if 'seed' in dp_param:
        np.random.seed(dp_param['seed'])

    mask, out = None, None
    if mode == 'train':
        mask = (np.random.rand(*x.shape) >= p) / (1 - p)
        out = x * mask
    elif mode == 'test':
        out = x
    out = out.astype(x.dtype, copy=False)
    return out, mask

def dropout_backward(dout, mask, mode):
    dx = None
    if mode == 'train':
        dx = dout * mask  # dout & mask has the same shape
    elif mode == 'test':
        dx = dout
    return dx
```

# Machine Learning

https://elitedatascience.com/machine-learning-interview-questions-answers

OpenCV

## SVM

https://zhuanlan.zhihu.com/p/99027375

https://blog.csdn.net/u010496169/article/details/73695164

### SVM v.s. LR

相同点：

LR和SVM都是分类算法。

如果不考虑核函数，LR和SVM都是线性分类算法，即分类决策面都是线性的。

LR和SVM都是监督学习算法。

不同点：

损失函数不同，LR是对数损失logloss，SVM是合页损失hinge loss。

LR受所有数据影响，而SVM只考虑局部的边界线附近的点（支持向量）。

![](/notes/ml/media/image1.png)
### Kernal Trick

## Naive Bayes

### Absolute Independence of Features

Q: What Is ‘naive’ in the Naive Bayes Classifier?

A: The classifier is called ‘naive’ because it makes assumptions that may or may not turn out to be correct. The algorithm assumes that the presence of one feature of a class is not related to the presence of any other feature (absolute independence of features), given the class variable.

## Logistic Regression

Loss Function Derivation

Formally, logistic regression model is

![](/notes/ml/media/image2.png)

solving for p gives ⇒ 

![](/notes/ml/media/image3.png)

⇒ likelihood:

![](/notes/ml/media/image4.png)

⇒ loss function

⇒ Derivation of log-likelihood for on data point (x, y):

![](/notes/ml/media/image5.png)

Note: 

Sigmoid derivation

![](/notes/ml/media/image6.png)

let h(x) = sigmoid(x)

⇒ d h(theta * x) / d theta = h(theta * x) (1 - h(theta * x)) * theta

## Decision Tree

https://medium.com/@rishabhjain_22692/decision-trees-it-begins-here-93ff54ef134

决策树问题 https://blog.csdn.net/qq_33011855/article/details/81478306

Splitting criterion

Entropy: measure the amount of uncertainty

![](/notes/ml/media/image7.png)

Information gain IG(A) is the measure of the difference in entropy from before to after the set S is split on an attribute A.

![](/notes/ml/media/image8.png)

https://zhuanlan.zhihu.com/p/30059442

### ID3 & C4.5 & CART

ID3 分类过细 ⇒ C4.5

CART 二叉树 / 分类回归树

ID3 是最早提出的决策树算法，他就是利用信息增益来选择特征的。

C4.5 是 ID3 的改进版，他不是直接使用信息增益，而是引入“信息增益比”指标作为特征的选择依据。

信息增益率: https://blog.csdn.net/u012351768/article/details/73469813

![](/notes/ml/media/image9.png)

何种情况下, 增益比比信息增益更可取? 当类别变量具有非常大的类别数量的时候

CART (Classification and Regression Tree) 即可用于分类也可用于回归问题。

CART 算法使用了基尼系数取代了信息熵模型。

### Pruning

预剪枝 / 后剪枝西瓜书例子

## Boosting / Bagging

Bagging 树每棵树都是独立的 v.s. Boosting 树之间不独立

Bagging & Boosting 

都是通过对弱学习器的结果进行综合来提升能力的方法

都没有超参数

随机森林组合弱学习器的结果，如果可能的话，树的数量越多越好

随机森林是一个黑盒子模型，不具备可解释性。

bagging适用于高的方差低偏差的模型，或者说复杂的模型

## Questions

https://github.com/MePlusYou/ML-Interview#dnn%E4%B8%BA%E4%BB%80%E4%B9%88%E5%8A%9F%E8%83%BD%E5%BC%BA%E5%A4%A7%E8%AF%B4%E8%AF%B4%E4%BD%A0%E7%9A%84%E7%90%86%E8%A7%A3

几个基础的 classifier

### Supervised v.s. Unsupervised

Supervised: labeled

Unsupervised: un-labeled; need to detect patterns, abnormal / outliers

### Metrics

@source

Classification Metrics (accuracy, precision, recall, F1-score, ROC, AUC, …)

Regression Metrics (MSE, MAE)

Ranking Metrics (MRR, DCG, NDCG)

Statistical Metrics (Correlation)

Computer Vision Metrics (PSNR, SSIM, IoU)

NLP Metrics (Perplexity, BLEU score)

Deep Learning Related Metrics (Inception score, Frechet Inception distance)

#### Classification Metrics: Precision \ Recall \ F1 \ Specificity \ Accuracy \ AUC \ ROC

![](/notes/ml/media/image10.png)
![](/notes/ml/media/image11.png)

Accuracy: (TP + TN) / (TP + TN + FP + FN)

Precision: TP / (TP + FP)

Recall: TP / (TP + FN)

Specificity: TN / (TN + FP)

F1-score: 2 / [1 / P + 1 / R] = 2 * PR / (P + R)

#### Regression Metrics: MSE \ MAE

MSE: Mean Squared Error

MAE: Mean Absolute Error (or mean absolute deviation) 

### Overfitting \ Underfitting

#### Q: How to find out Overfitting \ Underfitting

Overfitting: e.g., validation accuracy is much lower than training

Underfitting: e.g., both validation and training accuracy is low

> BUT, If your accuracy is low, how do you tell: whether your model is underfitting OR the problem itself is too challenging?

Build some stupid/simple baselines, to show how much your model improves based on that.

Note: Always use “training/validation” to discuss tuning. “Testing set” is not used for tuning. Once you trained your model well, it will be tested only once on the test set.

#### Q: CNN overfitting example

CNN w/ 2 FC

network:

filter size

L1 regularization

early stopping

FC dropout: make some inactive 

dataset: undersampling / oversampling

rotation / filpping

collecting more data 

7 x 7 filter

7 x 7

3 each, 3 x 3, in later layers

4 4 x 4

ResNet : predict residuals

residue connections

### Bias & Variance Tradeoff.

Predictive models have a tradeoff between bias (how well the model fits the data) and variance (how much the model changes based on changes in the inputs).

Bias

- Simpler models are stable (low variance) but they don't get close to the truth (high bias).

- Underfitting: High bias can cause an algorithm to miss the relevant relations between features and target outputs.

Variance

- More complex models are more prone to being overfit (high variance) but they are expressive enough to get close to the truth (low bias).

- Overfitting: High variance can cause an algorithm to model the random noise in the training data rather than the intended outputs.

The best model for a given problem usually lies somewhere in the middle.

### Regularization

L2 is more popular than L1?

L2:

+ close form solution / expression

+ more stable

L1:

– might have multiple answers

### Activations

![](/notes/ml/media/image12.png)

### Male Output between 0 - 1

softmax

sigmoid: vanishing gradients

during inference: clip 0 - 1

### Class Imbalance

- Use SVM instead; since SVM doesn’t care about the sample size of each class.

- Use weighted loss

- Oversampling \ Undersampling

E.g.: images: translation \ flipping \ rotation \ perspective transformation

### Object Detection

might or might not have a car

feat map from image

take the image, predict whether

bounding boxes

intersect with the car

after one epoch

hard negative mining

negative examples

-------

dropout：一大利器。

early stop：结合cross validation使用。

cross validation：当数据量较小的时候，应该是用来减轻 overfitting 最好的方式了吧。

当然，尽可能的扩大 training dataset 才是王道。

在训练之前记得 shuffle 一下数据集，一般是每次训练一个 epoch（就是把 training dataset 训练了一遍）后就 shuffle 一次，但是对于较大的数据集可以只 shuffle 一次，虽然这样会使得训练在第二个 epoch 就变得 biased，但是带来的好处可以 overcome 这种缺陷。

regularization

cross-validation

给例子 brainstorm features

large dataset 上的一些算法

logistic regression

Cost函数是什么

什么是overfitting, 如何detect，如何避免 

tree 的overfitting 

有哪些distance metrics 

Pvalue是什么 

k-means 算法具体怎么做的 

如何找outlier 

recommendation system 

similarity metrics

# Reinforcement Learning

Likelihood Ratio Policy Gradient Deduction

![](/notes/ml/media/image13.png)

https://medium.com/@jonathan_hui/rl-policy-gradients-explained-9b13b688b146

https://medium.com/@jonathan_hui/rl-policy-gradients-explained-advanced-topic-20c2b81a9a8b

### On-policy v.s. Off-policy

### Value-based v.s. Policy-based

https://blog.csdn.net/hnshahao/article/details/82969490

Why can subtract a baseline from REINFORCE: page 30

![](/notes/ml/media/image14.png)

## Imitation Learning

GAIL

## Inverse RL

https://towardsdatascience.com/inverse-reinforcement-learning-6453b7cdc90d

# from Roy Koganti (Apple) to Everyone:    10:50  AM

# Computer Vision

## Autonomous Driving

bounding box detection 

tracking

lane line coefficient regression

## Object Dectection

### R-CNN \ Faster R-CNN \ YOLO \ Mask R-CNN

mask R-CNN

region proposal network

## OpenCV

https://github.com/tobybreckon/python-examples-cv

https://github.com/PacktPublishing/OpenCV-3-x-with-Python-By-Example

## Filters

Box \ Guassian \ Sobel filter

## Datasets

### ImageNet Classification Challenge

- 1000 categories

- 1.2 million training images

- 50,000 validation images

- 150,000 testing images

- Top-5 error rate* of deep learning: 15.3%

- Top-5 error rate of second-best (which is non-deep learning): 26.2%

Note: Top-5 error rate: the fraction of test images for which the correct label is not among the five labels considered most probable by the model

# Natural Language Processing

Lookup Table

https://www.zhihu.com/question/61780787

Encode-Decoder

https://zhuanlan.zhihu.com/p/52106264

https://www.jianshu.com/p/50584e5e0e6a

# Optimization

Parallel v.s. Distributed Systems \\ CMU Courses: Distributed Systems / Parallel Architecture

## Parallelism

Potential problems

- Communication costs can dominate a parallel computation, severely limiting speedup

e.g.: significant amount of communication compared to computation

  - move machine/process locally near

- Imbalance in work assignment limited speedup

e.g.: Some processors ran out work to do (went idle), while others were still working on their assigned task 

Challenges

- partitioning \ communication \ synchronization

- machine characteristics are important

Parallel thinking

- Decomposing work into pieces that can safely be performed in parallel

- Assigning work to processors

- Managing communication/synchronization between the processors so that it does not limit speedup

Where is the parallelism? 

Different processors take radically different approaches

CPUs: Instruction-level parallelism (ILP): Implicit \ Fine-grain

- Pipelining & Superscalar

Work on multiple instructions at once

  - Fetch → Decode → Execute → Commit

- Out-of-order execution

Dynamically schedule instructions whenever they are “ready”

  - Dataflow increases parallelism by eliminating unnecessary dependencies. e.g.: True dependence: read-after-write

- Speculation: Guess what the program will do next to discover more independent work, “rolling back” incorrect guess

GPUs: Thread- & data-level parallelism: Explicit \ Coarse-grain

Performance Optimization

Optimizing the performance of parallel programs is an iterative process of refining choices for decomposition, assignment, and orchestration...

- Balance workload onto available execution resources

- Reduce communication (to avoid stalls)

- Reduce extra work (overhead) performed to increase parallelism, manage

assignment, reduce communication, etc.

Throughput v.s. Latency: trade off? no, different objectives \\ example

### Pipelining

- Instruction pipelines, (in CPUs) and other microprocessors to allow overlapping execution of multiple instructions with the same circuitry. The circuitry is usually divided up into stages and each stage processes a specific part of one instruction at a time, passing the partial results to the next stage. Examples of stages are instruction decode, arithmetic/logic and register fetch. They are related to the technologies of superscalar execution, operand forwarding, speculative execution and out-of-order execution.

- Graphics pipelines: found in most GPUs, which consist of multiple arithmetic units, or complete CPUs, that implement the various stages of common rendering operations (perspective projection, window clipping, color and light calculation, rendering, etc.). \\ Shader: GPUs

- Software pipelines, which consist of a sequence of computing processes (commands, program runs, tasks, threads, procedures, etc.), conceptually executed in parallel, with the output stream of one process being automatically fed as the input stream of the next one. The Unix system call pipe is a classic example of this concept.

### Cache

- Writing Policies

  - Write-through: write is done synchronously both to the cache and to the backing store / main memory.

  - Write-back / write-behind: initially, writing is done only to the cache. The write to the backing store is postponed until the modified content is about to be replaced by another cache block, i.e. the block being evicted.

- Hardware Caches

  - CPU: small memories on or close to the CPU can operate faster than the much larger main memory.

  - GPU: instruction caches for shaders

## NNs Compression

Pruning reduces the accuracy, so the network is trained further (known as fine-tuning) to recover; pruning & fine-tuning is often iterated to gradually reducing the network’s size.

Pruning Methods

- Structure

  - (unstructured pruning): remove individual parameters

  - (structured pruning) in groups, removing entire neurons, filters, or channels

- Scoring: absolute values, trained importance coefficients, or contributions to network activations or gradients.

  - Compare scores locally v.s. globally

- Scheduling

  - Prune all desired params in one step, v.s.

  - Prune a fixed fraction of the network iteratively

- Fine-tuning

Quantization

Quantization is a technique to reduce the number of bits needed to store each weight in the Neural Network through weight sharing, e.g.: Deep Compression

![](/notes/ml/media/image15.png)

# Resume

## Projects

### Auto-Scaling Policies

Designed an auto-scaling controller that adjusts the desired capacity of Auto-Scaling Group by monitoring workload metrics (e.g.: CPU utilization, memory utilization, disk reads/writes).

Parameters to tune: health check period / timeout /  cool down / warm up

Policy: scale in/out, step policy (to react to sudden surge/decrease)

### Parameter Server

Map-Reduce

```
# [ (w1_doc1, [c1, 1]), (w2_doc1, [c2, 1]), ..., 
    (w1_doc2, [c1, 1]), (w2_doc2, [c2, 1]), ...]
# after .collect(), vocabulary.collect() should look like: 
# [ (word1, (term_freq1, doc_freq1)), 
#   (word2, (term_freq2, doc_freq2)), ...]
```

Note: the operations that cause wide dependence require a shuﬄe.

Iteratively train Logistic Regression

d loss / d thetta = (y - sigmoid(x)) * theta ⇒ linear separable

### Job Scheduling

Pods v.s. Nodes

A Node is a virtual/physical worker machine in Kubernetes, depending on the cluster. 

A Node can have multiple pods, and the Kubernetes master automatically handles scheduling the pods across the Nodes in the cluster.

Goal: Kubernetes scheduler that considers heterogeneous cloud environments.

Diﬀerent jobs types

- MPI (Message Passing Interface) jobs:

assume distributed memory and have a tendency to exchange a lot of messages for synchronization. As a result, co-locating tasks of such jobs on the same rack will give them a performance advantage. 

- ML jobs (GPU jobs):

run much faster when the underlying machines have GPUs (while co-location within the same rack is not important).

Note: very short/fast GPU jobs doesn’t necessarily need GPU nodes (to save recources)

Scheduling Policies

FIFO Random \ FIFO Heterogeneous \ SJF Heterogeneous

- Consider slow v.s. fast run, depending on whether the job is run on preferred nodes.

- Utility: include the job arriving/waiting time

Analogy: cloud job scheduling & parallel execution designing

Execution units are specialized

- Floating-point (add/multiply): FPU / math coprocessor

- Integer (add/multiply/compare)

- Memory (load/store)

Processor designers must choose which execution units to include and how many

Structural hazard: Data is ready, but instr’n cannot issue because no hardware is available

### Malloclab

Malloc: Dynamic Storage Allocator Design

![](/notes/ml/media/image16.png)

![](/notes/ml/media/image17.png)
![](/notes/ml/media/image18.png)

- A general-purpose dynamic storage allocator, supports a full 64-bit address space.

- Implemented segregated list, footer & header strategy, optimized block placement & data structure for the external and internal fragment, increased performance using the doubly linked list for the allocator.

- Developed an efficient version of malloc, free, realloc and calloc packages

- Designed segregated free lists for memory requests of different ranges

- Designed special tiny fix-sized free block for requests of less than 16 bytes

- Optimized for correctness, space utilization and throughput

### Cache Locality

![](/notes/ml/media/image19.png)
![](/notes/ml/media/image20.png)
Optimize Matrix Multiplication for cache miss by utilizaing locality  

### Parallel 2D Grid Solver

A parallel programming example: 2D grid based solver

### Matrix-Vevtor Multiplication

O(mn/log(n))

### Compressive Sensing

Under some assumptions on L, S and the dimension of sampling space, one can exactly recover both low-rank and sparse components from undersampled measurements.

### NNs Compression

- Neural Nets

  - MobileNets: Open-Source Models for Efficient On-Device Vision

- Quantization: Deep Compression

  - Quantize the weights by using a codebook for each layer with 6 bits for all layers except the last fully connected layer which only has 5 bits.

- Pruning: Dynamic Network Surgery
