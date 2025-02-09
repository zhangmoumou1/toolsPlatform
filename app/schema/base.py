from app.excpetions.ParamsException import ParamsError


class QmsModel(object):

    @staticmethod
    def not_empty(v):
        if isinstance(v, str) and len(v.strip()) == 0:
            raise ParamsError("不能为空")
        if not isinstance(v, int):
            if not v:
                raise ParamsError("不能为空")
        return v

    @property
    def parameters(self):
        raise NotImplementedError
