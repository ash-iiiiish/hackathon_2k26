# Operating Systems — Unit Notes

## Process Management
A process is a program in execution. Each process has a Process Control Block (PCB) that stores its state, program counter, CPU registers, scheduling information and memory limits. A process moves through the states new, ready, running, waiting and terminated. The operating system switches between processes using a context switch, which saves the state of the current process in its PCB and loads the state of the next one. Context switching is pure overhead because the CPU does no useful work while switching.

Threads are lightweight units of execution inside a process. Threads of the same process share code, data and open files but have their own stack and registers. User-level threads are managed by a library, while kernel-level threads are scheduled by the operating system.

## CPU Scheduling
CPU scheduling decides which ready process gets the CPU next. Important criteria are CPU utilisation, throughput, turnaround time, waiting time and response time. First Come First Served (FCFS) is simple but suffers from the convoy effect, where short jobs wait behind a long job. Shortest Job First (SJF) gives the minimum average waiting time but needs the burst length in advance and can cause starvation. Round Robin gives every process a fixed time quantum; a very large quantum behaves like FCFS while a very small quantum causes too many context switches. Priority scheduling can starve low-priority processes, which is solved by aging, gradually increasing the priority of waiting processes.

Turnaround time equals completion time minus arrival time. Waiting time equals turnaround time minus burst time. Exam questions usually ask you to draw a Gantt chart and compute the average waiting time.

## Process Synchronization
A race condition happens when several processes access shared data concurrently and the result depends on the order of execution. The critical section problem requires mutual exclusion, progress and bounded waiting. Peterson's solution works for two processes using a flag array and a turn variable. A semaphore is an integer variable accessed only through the atomic operations wait and signal. A binary semaphore behaves like a mutex lock, while a counting semaphore controls access to a resource with several instances.

Classic problems include the producer-consumer problem with a bounded buffer, the readers-writers problem and the dining philosophers problem. Monitors are a higher-level construct where only one process can be active inside the monitor at a time.

## Deadlocks
A deadlock is a situation where a set of processes are blocked because each holds a resource and waits for a resource held by another. Four conditions must hold at the same time: mutual exclusion, hold and wait, no preemption and circular wait. Deadlock prevention breaks at least one of these conditions. Deadlock avoidance uses the Banker's algorithm, which grants a request only if the system stays in a safe state. A safe state means there is at least one safe sequence in which every process can finish. Deadlock detection uses a resource allocation graph or a wait-for graph, followed by recovery through process termination or resource preemption.

Banker's algorithm uses the Available, Max, Allocation and Need matrices, where Need equals Max minus Allocation. Numerical questions on the safety algorithm are very common in exams.

## Memory Management
Memory management keeps track of which parts of memory are in use and allocates memory to processes. Contiguous allocation suffers from external fragmentation, which compaction can reduce. Paging divides physical memory into fixed-size frames and logical memory into pages of the same size, removing external fragmentation but causing internal fragmentation. The page table maps page numbers to frame numbers. A Translation Lookaside Buffer (TLB) is a small fast cache of page table entries; effective access time depends on the TLB hit ratio.

Segmentation divides memory into variable-sized logical segments such as code, stack and heap. Each segment has a base and a limit stored in the segment table.

## Virtual Memory
Virtual memory lets a process run even when it is not completely in physical memory. Demand paging loads a page only when it is referenced; a reference to a page not in memory causes a page fault. Page replacement algorithms choose which page to evict. FIFO replaces the oldest page and can show Belady's anomaly, where more frames cause more page faults. The Optimal algorithm replaces the page that will not be used for the longest time and gives the fewest faults but is impossible to implement exactly. LRU replaces the least recently used page and is a practical approximation of Optimal.

Thrashing happens when a process spends more time paging than executing because it does not have enough frames. The working set model prevents thrashing by giving each process enough frames for its current locality.

## File Systems and Disk Scheduling
A file system provides a logical view of storage through files and directories. Allocation methods are contiguous, linked and indexed allocation. Indexed allocation uses an index block, like the inode in Unix, and supports direct access without external fragmentation. Disk scheduling reduces seek time. FCFS is fair but slow, SSTF picks the closest request but may starve far requests, SCAN moves the head end to end like an elevator, and C-SCAN returns to the start without servicing requests for a more uniform wait time.
