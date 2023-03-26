from rest_framework.serializers import ValidationError


def class_obj_validate(value: str, klass: object = None) -> object:
    if not str(value).isdecimal():
        raise ValidationError(f'Строка {value} должна содержать число.')
    if klass:
        obj = klass.objects.filter(id=value)
        if not obj:
            raise ValidationError(f'Объект {type(klass)} '
                                  f'с ID={value} не существует.')
        return obj[0]
    return None
