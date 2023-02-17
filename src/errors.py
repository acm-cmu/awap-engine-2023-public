""" INTERNAL ERRORS """

class InternalError(Exception):
    internal_msg = f"\n\n{'-'*60}\n" \
    "PLEASE REPORT INTERNAL ERRORS TO AWAP STAFF\n" \
    "Send the replay + map + bot files to acm-cmu@cs.cmu.edu\n" \
    f"{'-'*60}\n"
    def __init__(self, message):
        super().__init__(message + self.internal_msg)

class InvalidTileStateInternalError(InternalError):
    pass

class TerraformInternalError(InternalError):
    pass

class ExploreInternalError(InternalError):
    pass

class MineInternalError(InternalError):
    pass

class UnknownRobotInternalError(InternalError):
    pass

class IllegalMoveInternalError(InternalError):
    pass

class InvalidActionInternalError(InternalError):
    pass

""" USER ERRORS """

class UserError(Exception):
    pass

class IllegalActionError(UserError):
    pass

class IllegalSpawnError(UserError):
    pass

class IllegalTransformError(UserError):
    pass

class IllegalMoveError(UserError):
    pass


class InvalidBotFileError(UserError):
    pass

class InvalidMapError(UserError):
    pass

class UnknownRobotError(UserError):
    pass