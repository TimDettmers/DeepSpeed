import torch
import torch.distributed as dist
import apex
from deepspeed.utils import logger


def _initialize_parameter_parallel_groups(parameter_parallel_size=None):
    data_parallel_size = int(dist.get_world_size())
    parameter_parallel_size = parameter_parallel_size or data_parallel_size
    logger.info("data_parallel_size: %s, parameter_parallel_size: %s",
                data_parallel_size,
                parameter_parallel_size)
    assert data_parallel_size % parameter_parallel_size == 0, \
        'world size should be divisible by parameter parallel size'
    rank = dist.get_rank()
    my_group = None
    for i in range(data_parallel_size // parameter_parallel_size):
        ranks = range(i * parameter_parallel_size, (i + 1) * parameter_parallel_size)
        group = torch.distributed.new_group(ranks)
        if rank in ranks:
            my_group = group
    return my_group


ZERO_SUPPORTED_OPTIMIZERS = [torch.optim.Adam, apex.optimizers.FusedAdam]
try:
    from deepspeed.ops.adam import DeepSpeedCPUAdam
    ZERO_SUPPORTED_OPTIMIZERS.append(DeepSpeedCPUAdam)
except ImportError:
    print(
        "If trying to use DeepCPUAdam, please instal Ninja (apt-get install ninja-build) to use DeepCPUAdam in JIT mode."
    )


def is_zero_supported_optimizer(optimizer):
    print(
        f'Checking ZeRO support for optimizer={optimizer.__class__.__name__} type={type(optimizer)}'
    )
    return type(optimizer) in ZERO_SUPPORTED_OPTIMIZERS
