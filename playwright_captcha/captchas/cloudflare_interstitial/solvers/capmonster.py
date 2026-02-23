import logging

from playwright_captcha.solvers.api.capmonster import AsyncCapMonster
from playwright_captcha.utils.validators import validate_required_params

logger = logging.getLogger(__name__)


async def solve_cloudflare_interstitial_capmonster(async_capmonster_client: AsyncCapMonster, **kwargs) -> dict:
    """
    Solve Cloudflare Interstitial captcha using CapMonster service.

    :param async_capmonster_client: Instance of AsyncCapMonster client
    :param kwargs: Parameters for the CapMonster API call, e.g. 'sitekey', 'url'

    :return: Result of the captcha solving
    """

    logger.debug('Solving Cloudflare Interstitial captcha using CapMonster...')

    validate_required_params(['sitekey', 'url'], kwargs)

    result = await async_capmonster_client.turnstile(
        **kwargs
    )

    logger.debug(f'Solved Cloudflare Interstitial captcha: {result}')

    return result
