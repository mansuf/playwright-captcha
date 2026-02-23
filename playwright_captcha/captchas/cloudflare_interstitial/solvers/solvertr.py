import logging

from playwright_captcha.solvers.api.solvertr import AsyncSolverTr
from playwright_captcha.utils.validators import validate_required_params

logger = logging.getLogger(__name__)


async def solve_cloudflare_interstitial_solvertr(async_solvertr_client: AsyncSolverTr, **kwargs) -> dict:
    """
    Solve Cloudflare Interstitial captcha using Solver.tr service.

    :param async_solvertr_client: Instance of AsyncSolverTr client
    :param kwargs: Parameters for the Solver.tr API call, e.g. 'sitekey', 'url'

    :return: Result of the captcha solving
    """

    logger.debug('Solving Cloudflare Interstitial captcha using Solver.tr...')

    validate_required_params(['sitekey', 'url', 'action', 'data'], kwargs)

    result = await async_solvertr_client.turnstile(
        **kwargs
    )

    logger.debug(f'Solved Cloudflare Interstitial captcha: {result}')

    return result
