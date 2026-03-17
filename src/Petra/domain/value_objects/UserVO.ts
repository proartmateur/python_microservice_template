/**
 * @author Enrique Nieto <myself@example.com>
 * @date 2026-03-17 17:18:00.646250100 UTC
 */

/**
 * Value Object: UserVO
 * Encapsulates the user property with validation
 */
export class UserVO {
    private readonly _value: number;

    constructor(value: number) {
        this.validate(value);
        this._value = value;
    }

    get value(): number {
        return this._value;
    }

    private validate(value: number): void {
        // TODO: Add validation rules for user
        if (value === null || value === undefined) {
            throw new Error('UserVO cannot be null or undefined');
        }
    }

    public equals(other: UserVO): boolean {
        return this._value === other._value;
    }

    public toString(): string {
        return String(this._value);
    }
}
