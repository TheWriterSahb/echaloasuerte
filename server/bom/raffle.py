from collections import namedtuple
from random import shuffle
import logging

from django.utils.translation import ugettext_lazy as _
from django import template
from six import string_types

from server.bom.draw_base import BaseDraw, InvalidDraw


register = template.Library()
logger = logging.getLogger("echaloasuerte")


Participant = namedtuple('Participant', 'id name')


class RaffleDraw(BaseDraw):
    class RegistrationError(Exception):
        """
        Exception thrown when an user can not be registered as participant
        """
        pass
    class AlreadyRegisteredError(Exception):
        """
        Exception thrown when an user can not be registered as participant
        """
        pass
    RESTRICTED = 'restricted'
    FACEBOOK = 'facebook'
    REGISTRATION_CHOICES = ((RESTRICTED, _('Restricted')),
                            (FACEBOOK, _('Facebook')),
                            )
    LOGIN = 'login'
    SHARE = 'share'
    REGISTRATION_REQUIREMENT_CHOICES = ((LOGIN, _('Log in Facebook')),
                                        (SHARE, _('Share in Facebook')),
                                        )

    TYPES = BaseDraw.TYPES.copy()
    TYPES['prices'] = list
    TYPES['participants'] = list
    TYPES['registration_type'] = string_types

    def __init__(self, prices=None, participants=None, registration_type=RESTRICTED, registration_requirement=LOGIN, **kwargs):
        super(RaffleDraw, self).__init__(**kwargs)

        self.prices = prices if prices else []
        """List of prices"""

        self.registration_type = registration_type

        if registration_type == RaffleDraw.FACEBOOK:
            participants = participants or []
            # Initialize participants with __dict__ to bypass the setter
            self.__dict__['participants'] = []
            for participant in participants:
                if isinstance(participant, string_types):
                    participant = participant.strip()
                    id_ = participant.split(':')[0].replace('{', '')
                    value = participant.split(':')[1].replace('}', '')
                    participant = [id_, value]
                self.participants.append(Participant(*participant))
            """List of participants"""
            self.registration_requirement = registration_requirement
            """The action required to register in the draw"""
        else:
            self.participants = participants if participants else []
            self.registration_requirement = None

    @property
    def participants(self):
        return self.__dict__['participants']

    @participants.setter
    def participants(self, participants):
        """
        In Facebook raffle, the list or participants can't be set.
        Participants can only by edited by the 'append' or 'remove' methods of the dict
        Pass silently, any exception is thrown.
        """
        if self.registration_type != self.FACEBOOK:
            self.__dict__['participants'] = participants

    def validate(self):
        super(RaffleDraw, self).validate()
        if not self.prices:
            raise InvalidDraw('prices')

    def is_feasible(self):
        return self.prices and self.participants

    def generate_result(self):
        participants = self.participants
        shuffle(participants)
        return list(zip(self.prices, participants))

    def register_participant(self, new_participant):
        if self.registration_type != self.FACEBOOK:
            raise RaffleDraw.RegistrationError("Canot register in a non FB draw")
        if any(participant.id == new_participant.id for participant in self.participants):
            raise RaffleDraw.AlreadyRegisteredError("User already registered")
        self.participants.append(new_participant)


