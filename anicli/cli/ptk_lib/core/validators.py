from typing import TYPE_CHECKING, Optional

from prompt_toolkit.validation import ValidationError
from prompt_toolkit.validation import Validator as PTValidator

from .types import T_FSM_VALIDATOR, FSMContext

if TYPE_CHECKING:
    from .fsm import BaseFSM


class CallableWrapperValidator(PTValidator):
    """Validator that uses static validator if available, otherwise dynamic validator from FSM.

    Args:
        validator_func: Optional static validator function
        fsm_context: FSM context for validation
        fsm_instance: Optional FSM instance for dynamic validation
        state_name: Optional state name for dynamic validation
    """

    def __init__(
        self,
        validator_func: Optional[T_FSM_VALIDATOR],
        fsm_context: FSMContext,
        fsm_instance: Optional["BaseFSM"] = None,
        state_name: Optional[str] = None,
    ) -> None:
        self.validator_func = validator_func
        self.fsm_context = fsm_context
        self.fsm_instance = fsm_instance
        self.state_name = state_name

        if fsm_instance and state_name:
            self.validator = HybridFSMValidator(validator_func, fsm_instance, state_name)
        else:
            self.validator = None

    def validate(self, document):
        """Validate the input document using either static or dynamic validation.

        Args:
            document: The document to validate

        Raises:
            ValidationError: If validation fails
        """
        text = document.text
        try:
            if self.validator:
                # hybrid validator (static priority + dynamic as fallback)
                is_valid = self.validator(text, self.fsm_context)
                if not is_valid:
                    error_msg = self.validator.get_error_message(text, self.fsm_context) or "Invalid input"
                    raise ValidationError(message=error_msg, cursor_position=len(text))
            elif self.validator_func:
                # static validator only
                is_valid = self.validator_func(text, self.fsm_context)
                if not is_valid:
                    raise ValidationError(message="Invalid input", cursor_position=len(text))
            # other valid
        except Exception as e:
            raise ValidationError(message=str(e), cursor_position=len(text))  # noqa: B904


class HybridFSMValidator:
    """Validator that uses static validator if provided, otherwise dynamic validator from FSM.

    Args:
        static_validator: Optional static validator function with priority
        fsm_instance: FSM instance for dynamic validation
        state_name: Name of the state for dynamic validation
    """

    def __init__(self, static_validator: Optional[T_FSM_VALIDATOR], fsm_instance: "BaseFSM", state_name: str):
        self.static_validator = static_validator
        self.fsm_instance = fsm_instance
        self.state_name = state_name

    def __call__(self, user_input: str, fsm_context: FSMContext) -> bool:
        """Validate user input using either static or dynamic validation.

        Args:
            user_input: The input string to validate
            fsm_context: The FSM context for validation

        Returns:
            bool: True if validation passes, False otherwise
        """
        # static validator has absolute priority
        if self.static_validator:
            return self.static_validator(user_input, fsm_context)

        return self._validate_dynamic(user_input, fsm_context)

    def _validate_dynamic(self, user_input: str, _fsm_context: FSMContext) -> bool:
        """Perform dynamic validation using the FSM instance.

        Args:
            user_input: The input string to validate
            _fsm_context: The FSM context for validation (unused)

        Returns:
            bool: True if validation passes, False otherwise
        """
        dynamic_result = self.fsm_instance.get_dynamic_validator(self.state_name, user_input)

        if dynamic_result is None:
            return True
        elif isinstance(dynamic_result, bool):
            return dynamic_result
        elif isinstance(dynamic_result, str):
            self._last_dynamic_error = dynamic_result
            return False
        else:
            return True

    def get_error_message(self, user_input: str, fsm_context: FSMContext) -> Optional[str]:
        """Get the error message for invalid input.

        Args:
            user_input: The input string that failed validation
            fsm_context: The FSM context for validation

        Returns:
            Optional[str]: Error message if validation failed, None otherwise
        """
        if self.static_validator:
            static_result = self.static_validator(user_input, fsm_context)
            if not static_result:
                return "Invalid input"
            return None

        dynamic_result = self.fsm_instance.get_dynamic_validator(self.state_name, user_input)
        if isinstance(dynamic_result, str):
            return dynamic_result
        elif dynamic_result is False:
            return "Invalid input"
        return None
