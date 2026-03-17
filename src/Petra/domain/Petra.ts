/**
 * @author Enrique Nieto <myself@example.com>
 * @date 2026-03-17 17:18:00.646250100 UTC
 */

import { NameVO } from "/src/Petra/domain/value_objects/NameVO"
import { UserVO } from "/src/Petra/domain/value_objects/UserVO"

/**
 * Domain Model: Petra
 * Represents the core business entity
 */
export class Petra {
   private _name: NameVO;
   private _user: UserVO;


    constructor(
       name: NameVO,
       user: UserVO,

    ) {
       this._name = name;
       this._user = user;

    }

    // Getters
   get name(): NameVO {
        return this._name;
    }

   get user(): UserVO {
        return this._user;
    }



    // Business logic methods
    public validate(): boolean {
        // TODO: Implement validation logic
        return true;
    }

    public toJSON(): object {
        return {
           name: this._name.value,
           user: this._user.value,

        };
    }
}
