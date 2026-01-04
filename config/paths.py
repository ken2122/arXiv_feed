from dataclasses import dataclass
from pathlib import Path
from datetime import date

@dataclass(frozen=True)
class DataPathRule:
    base_dir: Path = Path("data")

    def build(
        self,
        target_date: date,
        data_type: str,
        file_name: str,
    ) -> Path:
        yyyy = target_date.strftime("%Y")
        mm = target_date.strftime("%m")
        timestamp = target_date.strftime("%Y%m%d_%H%M%S")

        return (
            self.base_dir
            / f"{yyyy}/{mm}"
            / data_type
            / f"{file_name}_{timestamp}.{data_type}"
        )

# グローバルで 1 度だけ生成
DATA_PATH_RULE = DataPathRule()
