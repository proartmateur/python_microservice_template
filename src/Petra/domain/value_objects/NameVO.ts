/**
 * @author Enrique Nieto <myself@example.com>
 * @date 2026-03-17 17:18:00.646250100 UTC
 */

/**
 * Value Object: NameVO
 * Encapsulates the name property with validation
 */
export class NameVO {
    private readonly _value: string;

    constructor(value: string) {
        this.validate(value);
        this._value = value;
    }

    get value(): string {
        return this._value;
    }

    private validate(value: string): void {
        // TODO: Add validation rules for name
        if (value === null || value === undefined) {
            throw new Error('NameVO cannot be null or undefined');
        }
    }

    public equals(other: NameVO): boolean {
        return this._value === other._value;
    }

    public toString(): string {
        return String(this._value);
    }
}
